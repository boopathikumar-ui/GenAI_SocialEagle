"""User settings endpoints."""
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.rate_limit import limiter
from app.schemas.dashboard import VisibilityResult, VisibilityUpdate
from app.services.dashboard_service import DashboardService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settings", tags=["settings"])

DbDep = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.put("/roasts-visibility", response_model=VisibilityResult)
@limiter.limit("10/minute")
async def set_roasts_visibility(
    request: Request,
    payload: VisibilityUpdate,
    db: DbDep,
    user: CurrentUser,
) -> VisibilityResult:
    """Make all of the current user's roasts public or private."""
    updated = DashboardService(db).set_all_visibility(user.id, payload.is_public)
    return VisibilityResult(updated=updated)
