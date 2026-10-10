"""Authentication business logic."""
import logging
from datetime import UTC, datetime
from urllib.parse import urlencode

import httpx
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.auth.security import (
    DUMMY_PASSWORD_HASH,
    REFRESH,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password_async,
    hash_token,
    verify_password_async,
)
from app.config import settings
from app.exceptions import ConflictError, ExternalServiceError, ForbiddenError, UnauthorizedError
from app.models.user import RefreshToken, User
from app.schemas.auth import TokenPair

logger = logging.getLogger(__name__)

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def get_user_by_email(db: Session, email: str) -> User | None:
    """Look up a user by (case-insensitive) email."""
    return db.scalar(select(User).where(User.email == _normalize_email(email)))


def issue_tokens(db: Session, user: User) -> TokenPair:
    """Create an access/refresh pair and persist the refresh token hash."""
    access = create_access_token(user.id)
    refresh, expires_at = create_refresh_token(user.id)
    db.add(RefreshToken(user_id=user.id, token=hash_token(refresh), expires_at=expires_at))
    db.commit()
    return TokenPair(access_token=access, refresh_token=refresh)


async def register_user(db: Session, email: str, password: str, full_name: str) -> User:
    """Create a new password-based user."""
    if get_user_by_email(db, email) is not None:
        raise ConflictError("Email already registered")
    user = User(
        email=_normalize_email(email),
        hashed_password=await hash_password_async(password),
        full_name=full_name.strip(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info("Registered user id=%s", user.id)
    return user


async def authenticate(db: Session, email: str, password: str) -> User:
    """Validate credentials and return the user (constant-ish time for unknown users)."""
    user = get_user_by_email(db, email)
    hashed = user.hashed_password if user is not None else None
    # Always run one bcrypt verify so unknown users/OAuth-only accounts are not distinguishable.
    valid = await verify_password_async(password, hashed or DUMMY_PASSWORD_HASH)
    if user is None or not hashed or not valid:
        raise UnauthorizedError("Invalid email or password")
    if not user.is_active:
        raise ForbiddenError("Account is disabled")
    return user


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def revoke_all_refresh_tokens(db: Session, user_id: int) -> None:
    """Revoke every outstanding refresh token of a user (caller commits)."""
    db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user_id, RefreshToken.revoked.is_(False))
        .values(revoked=True)
    )


def rotate_refresh_token(db: Session, refresh_token: str) -> TokenPair:
    """Atomically validate, revoke and replace a refresh token.

    Reuse of an already-revoked token is treated as theft: all of the user's
    refresh tokens are revoked.
    """
    if decode_token(refresh_token, REFRESH) is None:
        raise UnauthorizedError("Invalid refresh token")
    token_hash = hash_token(refresh_token)
    stored = db.scalar(select(RefreshToken).where(RefreshToken.token == token_hash))
    if stored is None:
        raise UnauthorizedError("Invalid refresh token")
    if stored.revoked:
        logger.warning("Refresh token reuse detected for user id=%s", stored.user_id)
        revoke_all_refresh_tokens(db, stored.user_id)
        db.commit()
        raise UnauthorizedError("Invalid refresh token")
    if _aware(stored.expires_at) <= datetime.now(UTC):
        raise UnauthorizedError("Invalid refresh token")
    user = db.get(User, stored.user_id)
    if user is None or not user.is_active:
        raise UnauthorizedError("Invalid refresh token")
    # Compare-and-set: only one concurrent request can flip revoked False -> True.
    result = db.execute(
        update(RefreshToken)
        .where(RefreshToken.token == token_hash, RefreshToken.revoked.is_(False))
        .values(revoked=True)
    )
    if result.rowcount != 1:  # type: ignore[attr-defined]
        logger.warning("Concurrent refresh token reuse for user id=%s", user.id)
        db.rollback()
        revoke_all_refresh_tokens(db, user.id)
        db.commit()
        raise UnauthorizedError("Invalid refresh token")
    return issue_tokens(db, user)


def revoke_refresh_token(db: Session, refresh_token: str) -> None:
    """Revoke a refresh token if known (idempotent)."""
    stored = db.scalar(select(RefreshToken).where(RefreshToken.token == hash_token(refresh_token)))
    if stored is not None and not stored.revoked:
        stored.revoked = True
        db.commit()


def update_profile(db: Session, user: User, full_name: str) -> User:
    """Update the user's display name."""
    user.full_name = full_name.strip()
    db.commit()
    db.refresh(user)
    return user


def google_authorize_url(state: str, redirect_uri: str) -> str:
    """Build the Google OAuth consent URL."""
    if not settings.GOOGLE_CLIENT_ID:
        raise ExternalServiceError("Google OAuth is not configured")
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "online",
        "prompt": "select_account",
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


async def google_fetch_profile(code: str, redirect_uri: str) -> dict[str, object]:
    """Exchange an authorization code for the Google user profile."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            token_resp = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "code": code,
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                },
            )
            token_resp.raise_for_status()
            access = token_resp.json()["access_token"]
            info_resp = await client.get(
                GOOGLE_USERINFO_URL, headers={"Authorization": f"Bearer {access}"}
            )
            info_resp.raise_for_status()
            profile: dict[str, object] = info_resp.json()
    except (httpx.HTTPError, KeyError, ValueError) as exc:
        logger.warning("Google OAuth exchange failed: %s", exc)
        raise ExternalServiceError("Google authentication failed") from exc
    return profile


def upsert_google_user(db: Session, profile: dict[str, object]) -> User:
    """Create or fetch a user from a Google profile (email must be verified)."""
    email = profile.get("email")
    if not isinstance(email, str) or not email or profile.get("email_verified") is not True:
        raise UnauthorizedError("Google account email is not verified")
    name = profile.get("name")
    user = get_user_by_email(db, email)
    if user is None:
        user = User(
            email=_normalize_email(email),
            full_name=name if isinstance(name, str) else None,
            is_verified=True,
            oauth_provider="google",
        )
        db.add(user)
    else:
        if not user.is_active:
            raise ForbiddenError("Account is disabled")
        user.is_verified = True
        if user.hashed_password is not None:
            # Account takeover mitigation: linking Google to a password account drops the
            # password (it may have been set by someone who never owned the mailbox) and
            # signs out every existing session.
            user.hashed_password = None
            revoke_all_refresh_tokens(db, user.id)
        if user.oauth_provider is None:
            user.oauth_provider = "google"
    db.commit()
    db.refresh(user)
    return user
