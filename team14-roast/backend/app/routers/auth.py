"""Authentication routes."""
import logging
import secrets
from typing import Annotated
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Query, Request, Response, status
from fastapi.responses import RedirectResponse
import jwt
from sqlalchemy.orm import Session

from app.config import ALGORITHM, settings
from app.dependencies import get_current_user, get_db
from app.exceptions import AppError
from app.models.user import User
from app.rate_limit import limiter
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenPair,
    UpdateProfileRequest,
    UserOut,
)
from app.services import auth_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

STATE_COOKIE = "oauth_state"
STATE_TTL_SECONDS = 600


def _redirect_uri(request: Request) -> str:
    if settings.GOOGLE_REDIRECT_URI:
        return settings.GOOGLE_REDIRECT_URI
    return str(request.url_for("google_callback"))


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def register(
    request: Request, payload: RegisterRequest, db: Annotated[Session, Depends(get_db)]
) -> AuthResponse:
    """Create an account and return tokens."""
    user = await auth_service.register_user(db, payload.email, payload.password, payload.full_name)
    tokens = auth_service.issue_tokens(db, user)
    return AuthResponse(**tokens.model_dump(), user=UserOut.model_validate(user))


@router.post("/login", response_model=AuthResponse)
@limiter.limit("10/minute")
async def login(
    request: Request, payload: LoginRequest, db: Annotated[Session, Depends(get_db)]
) -> AuthResponse:
    """Authenticate with email and password."""
    user = await auth_service.authenticate(db, payload.email, payload.password)
    tokens = auth_service.issue_tokens(db, user)
    return AuthResponse(**tokens.model_dump(), user=UserOut.model_validate(user))


@router.post("/refresh", response_model=TokenPair)
@limiter.limit("10/minute")
async def refresh(
    request: Request, payload: RefreshRequest, db: Annotated[Session, Depends(get_db)]
) -> TokenPair:
    """Rotate a refresh token and issue a new pair."""
    return auth_service.rotate_refresh_token(db, payload.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(payload: RefreshRequest, db: Annotated[Session, Depends(get_db)]) -> Response:
    """Revoke the given refresh token."""
    auth_service.revoke_refresh_token(db, payload.refresh_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=UserOut)
async def me(user: Annotated[User, Depends(get_current_user)]) -> User:
    """Return the current user."""
    return user


@router.put("/me", response_model=UserOut)
async def update_me(
    payload: UpdateProfileRequest,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """Update the current user's profile."""
    return auth_service.update_profile(db, user, payload.full_name)


@router.get("/google")
async def google_login(request: Request) -> RedirectResponse:
    """Redirect to Google's consent screen with a CSRF state."""
    state = secrets.token_urlsafe(32)
    url = auth_service.google_authorize_url(state, _redirect_uri(request))
    response = RedirectResponse(url)
    response.set_cookie(
        STATE_COOKIE,
        jwt.encode({"nonce": state}, settings.SECRET_KEY, algorithm=ALGORITHM),
        max_age=STATE_TTL_SECONDS,
        httponly=True,
        samesite="lax",
        secure=not settings.DEBUG,
    )
    return response


@router.get("/google/callback", name="google_callback")
async def google_callback(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    code: Annotated[str | None, Query()] = None,
    state: Annotated[str | None, Query()] = None,
    error: Annotated[str | None, Query()] = None,
) -> RedirectResponse:
    """Handle the Google callback, upsert the user and redirect to the frontend."""
    failure = RedirectResponse(
        f"{settings.FRONTEND_URL.rstrip('/')}/login?error=oauth_failed", status_code=302
    )
    failure.delete_cookie(STATE_COOKIE)
    cookie = request.cookies.get(STATE_COOKIE)
    nonce: object = None
    if cookie:
        try:
            nonce = jwt.decode(cookie, settings.SECRET_KEY, algorithms=[ALGORITHM]).get("nonce")
        except jwt.PyJWTError:
            nonce = None
    if (
        error
        or not code
        or not state
        or not isinstance(nonce, str)
        or not secrets.compare_digest(nonce, state)
    ):
        # Never log raw query values (code/state/error are attacker-controlled).
        logger.warning("Google OAuth callback rejected (provider_error=%s)", bool(error))
        return failure
    try:
        profile = await auth_service.google_fetch_profile(code, _redirect_uri(request))
        user = auth_service.upsert_google_user(db, profile)
        tokens = auth_service.issue_tokens(db, user)
    except AppError as exc:
        logger.warning("Google OAuth callback failed (%s)", exc.code)
        return failure
    # Tokens go in the URL fragment so they are never sent to servers or logged in referrers.
    fragment = urlencode(
        {"access_token": tokens.access_token, "refresh_token": tokens.refresh_token}
    )
    response = RedirectResponse(
        f"{settings.FRONTEND_URL.rstrip('/')}/auth/callback#{fragment}", status_code=302
    )
    response.delete_cookie(STATE_COOKIE)
    return response
