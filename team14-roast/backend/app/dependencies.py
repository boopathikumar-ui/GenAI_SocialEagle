"""Shared FastAPI dependencies."""
import logging
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth.security import ACCESS, decode_token
from app.database import get_db
from app.exceptions import UnauthorizedError
from app.models.user import User

logger = logging.getLogger(__name__)

bearer_scheme = HTTPBearer(auto_error=False)

__all__ = ["get_db", "get_current_user", "get_optional_user"]


def _resolve_user(credentials: HTTPAuthorizationCredentials | None, db: Session) -> User | None:
    if credentials is None:
        return None
    claims = decode_token(credentials.credentials, ACCESS)
    if claims is None:
        return None
    user = db.get(User, int(claims["sub"]))
    if user is None or not user.is_active:
        return None
    return user


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """Resolve the Bearer access token to an active User or raise UnauthorizedError."""
    user = _resolve_user(credentials, db)
    if user is None:
        raise UnauthorizedError("Invalid or missing credentials")
    return user


async def get_optional_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User | None:
    """Return the user if a valid Bearer token is supplied, else None."""
    return _resolve_user(credentials, db)
