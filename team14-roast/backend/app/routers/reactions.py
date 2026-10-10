"""Reaction endpoints."""
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.rate_limit import limiter
from app.schemas.gallery import EmojiName, ReactionCreate, ReactionState
from app.services.gallery_service import GalleryService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/roasts", tags=["reactions"])


@router.post("/{roast_id}/reactions", response_model=ReactionState)
@limiter.limit("60/minute")
async def add_reaction(
    request: Request,
    roast_id: int,
    payload: ReactionCreate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> ReactionState:
    """Add the current user's reaction (idempotent)."""
    return GalleryService(db).add_reaction(roast_id, payload.emoji, user)


@router.delete("/{roast_id}/reactions/{emoji}", response_model=ReactionState)
async def remove_reaction(
    roast_id: int,
    emoji: EmojiName,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> ReactionState:
    """Remove the current user's reaction."""
    return GalleryService(db).remove_reaction(roast_id, emoji, user)
