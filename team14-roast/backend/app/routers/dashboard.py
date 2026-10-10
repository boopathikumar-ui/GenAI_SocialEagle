"""Dashboard endpoints."""
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.dashboard import DashboardStats
from app.services.dashboard_service import DashboardService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

DbDep = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.get("/stats", response_model=DashboardStats)
async def get_stats(
    db: DbDep,
    user: CurrentUser,
    days: Annotated[int, Query(ge=7, le=90)] = 30,
) -> DashboardStats:
    """Return the current user's dashboard statistics."""
    return DashboardService(db).stats(user.id, days)
