"""Password hashing and JWT helpers."""
import hashlib
import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt
from starlette.concurrency import run_in_threadpool

from app.config import ALGORITHM, settings

logger = logging.getLogger(__name__)

ACCESS = "access"
REFRESH = "refresh"


def hash_password(password: str) -> str:
    """Return a bcrypt hash of the given password."""
    return bcrypt.hashpw(password.encode("utf-8")[:72], bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """Check a plain password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(password.encode("utf-8")[:72], hashed.encode("utf-8"))
    except ValueError:
        return False


async def hash_password_async(password: str) -> str:
    """bcrypt hash off the event loop."""
    return await run_in_threadpool(hash_password, password)


async def verify_password_async(password: str, hashed: str) -> bool:
    """bcrypt verify off the event loop."""
    return await run_in_threadpool(verify_password, password, hashed)


# Fixed bcrypt hash (of a random throwaway value) used to equalise login timing
# when the email is unknown or the account has no password.
DUMMY_PASSWORD_HASH = "$2b$12$.KtEc8uQkpCEYm2Xu3FZ8.w3NyrMsd5ME9xjfyQV8yfBj16uDlHL6"


def hash_token(token: str) -> str:
    """Return the SHA-256 hex digest of a token (stored instead of the raw value)."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _create_token(subject: int, token_type: str, expires_delta: timedelta) -> tuple[str, datetime]:
    expires_at = datetime.now(UTC) + expires_delta
    payload: dict[str, Any] = {
        "sub": str(subject),
        "type": token_type,
        "exp": expires_at,
        "iat": datetime.now(UTC),
        "jti": uuid.uuid4().hex,
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)
    return token, expires_at


def create_access_token(user_id: int) -> str:
    """Create a signed access JWT (default 30 minutes)."""
    token, _ = _create_token(
        user_id, ACCESS, timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return token


def create_refresh_token(user_id: int) -> tuple[str, datetime]:
    """Create a signed refresh JWT (default 7 days); returns (token, expires_at)."""
    return _create_token(user_id, REFRESH, timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS))


def decode_token(token: str, expected_type: str) -> dict[str, Any] | None:
    """Decode and validate a JWT of the expected type; return claims or None."""
    try:
        claims: dict[str, Any] = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[ALGORITHM]
        )
    except jwt.PyJWTError:
        return None
    if claims.get("type") != expected_type or not str(claims.get("sub", "")).isdigit():
        return None
    return claims
