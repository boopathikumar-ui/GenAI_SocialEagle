"""Public gallery endpoint."""
import logging
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_optional_user
from app.models.user import User
from app.schemas.gallery import GalleryPage
from app.services.gallery_service import GalleryService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/gallery", tags=["gallery"])


@router.get("", response_model=GalleryPage)
async def list_gallery(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User | None, Depends(get_optional_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 12,
    sort: Literal["new", "top"] = "new",
) -> GalleryPage:
    """List public roasts, newest or most reacted."""
    return GalleryService(db).list_public(page, page_size, sort, user)
