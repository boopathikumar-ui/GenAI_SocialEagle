"""Roast endpoints."""
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.dependencies import get_current_user, get_db, get_optional_user
from app.schemas.roast import RoastCreate, RoastList, RoastRead, RoastUpdate
from app.services.roast_service import RoastService

from slowapi.util import get_remote_address

from app.rate_limit import limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/roasts", tags=["roasts"])

DbDep = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalUser = Annotated[User | None, Depends(get_optional_user)]


@router.post("", response_model=RoastRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def create_roast(
    request: Request,
    payload: RoastCreate,
    db: DbDep,
    user: OptionalUser,
) -> RoastRead:
    roast = await RoastService(db).create_roast(
        payload.github_url,
        payload.intensity,
        payload.is_public,
        user,
        client_ip=get_remote_address(request),
        language=payload.language,
    )
    return RoastRead.model_validate(roast)


@router.get("", response_model=RoastList)
async def list_roasts(
    db: DbDep,
    user: CurrentUser,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 10,
) -> RoastList:
    items, total = RoastService(db).list_for_user(user.id, page, page_size)
    return RoastList(
        items=[RoastRead.model_validate(r) for r in items],
        total=total,
        page=page,
        page_size=page_size,
    )


# Declared before /{roast_id} so "s" is never parsed as an id.
@router.get("/s/{slug}", response_model=RoastRead)
async def get_shared_roast(slug: str, db: DbDep) -> RoastRead:
    return RoastRead.model_validate(RoastService(db).get_public_by_slug(slug))


@router.get("/{roast_id}", response_model=RoastRead)
async def get_roast(roast_id: int, db: DbDep, user: CurrentUser) -> RoastRead:
    return RoastRead.model_validate(RoastService(db).get_owned(roast_id, user.id))


@router.delete("/{roast_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_roast(roast_id: int, db: DbDep, user: CurrentUser) -> Response:
    service = RoastService(db)
    service.delete(service.get_owned(roast_id, user.id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/{roast_id}", response_model=RoastRead)
async def update_roast(
    roast_id: int, payload: RoastUpdate, db: DbDep, user: CurrentUser
) -> RoastRead:
    service = RoastService(db)
    roast = service.set_public(service.get_owned(roast_id, user.id), payload.is_public)
    return RoastRead.model_validate(roast)
