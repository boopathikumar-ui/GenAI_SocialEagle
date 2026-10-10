"""Gallery listing and reactions."""
import logging
from collections import defaultdict
from typing import Any, Literal, cast

from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.exceptions import NotFoundError
from app.models.reaction import Reaction, ReactionEmoji
from app.models.roast import Roast
from app.models.user import User
from app.schemas.gallery import (
    EmojiName,
    GalleryPage,
    GalleryRoast,
    ReactionCounts,
    ReactionState,
)

logger = logging.getLogger(__name__)

SortMode = Literal["new", "top"]


class GalleryService:
    """Reads public roasts with reaction aggregates and manages reactions."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def _aggregates(
        self, roast_ids: list[int], user_id: int | None
    ) -> tuple[dict[int, dict[str, int]], dict[int, list[EmojiName]]]:
        """Counts per roast/emoji (one grouped query) and the user's emoji (one query)."""
        counts: dict[int, dict[str, int]] = defaultdict(dict)
        mine: dict[int, list[EmojiName]] = defaultdict(list)
        if not roast_ids:
            return counts, mine
        rows = self.db.execute(
            select(Reaction.roast_id, Reaction.emoji, func.count())
            .where(Reaction.roast_id.in_(roast_ids))
            .group_by(Reaction.roast_id, Reaction.emoji)
        ).all()
        for roast_id, emoji, n in rows:
            counts[roast_id][emoji.value] = n
        if user_id is not None:
            own = self.db.execute(
                select(Reaction.roast_id, Reaction.emoji)
                .where(Reaction.roast_id.in_(roast_ids), Reaction.user_id == user_id)
                .order_by(Reaction.id)
            ).all()
            for roast_id, emoji in own:
                mine[roast_id].append(cast(EmojiName, emoji.value))
        return counts, mine

    def list_public(
        self, page: int, page_size: int, sort: SortMode, user: User | None
    ) -> GalleryPage:
        """Return one page of public roasts."""
        total = (
            self.db.scalar(select(func.count()).select_from(Roast).where(Roast.is_public.is_(True)))
            or 0
        )
        stmt: Any = select(Roast).where(Roast.is_public.is_(True))
        if sort == "top":
            totals = (
                select(Reaction.roast_id.label("rid"), func.count().label("n"))
                .group_by(Reaction.roast_id)
                .subquery()
            )
            stmt = stmt.outerjoin(totals, totals.c.rid == Roast.id).order_by(
                func.coalesce(totals.c.n, 0).desc(), Roast.created_at.desc(), Roast.id.desc()
            )
        else:
            stmt = stmt.order_by(Roast.created_at.desc(), Roast.id.desc())
        roasts = list(self.db.scalars(stmt.limit(page_size).offset((page - 1) * page_size)).all())
        counts, mine = self._aggregates([r.id for r in roasts], user.id if user else None)
        items = [
            GalleryRoast(
                id=r.id,
                github_username=r.github_username,
                target_type=r.target_type.value,
                intensity=r.intensity.value,
                roast_text=r.roast_text,
                share_slug=r.share_slug,
                created_at=r.created_at,
                reaction_counts=ReactionCounts(**counts[r.id]),
                my_reactions=mine[r.id],
            )
            for r in roasts
        ]
        return GalleryPage(items=items, total=total, page=page, page_size=page_size)

    def _visible_roast(self, roast_id: int, user: User) -> Roast:
        roast = self.db.get(Roast, roast_id)
        if roast is None or not (roast.is_public or roast.user_id == user.id):
            raise NotFoundError("Roast not found")
        return roast

    def state(self, roast_id: int, user: User) -> ReactionState:
        """Current counts and the user's reactions for a roast."""
        counts, mine = self._aggregates([roast_id], user.id)
        return ReactionState(
            reaction_counts=ReactionCounts(**counts[roast_id]),
            my_reactions=mine[roast_id],
        )

    def add_reaction(self, roast_id: int, emoji: str, user: User) -> ReactionState:
        """Add a reaction; idempotent, race-safe via the unique constraint."""
        self._visible_roast(roast_id, user)
        user_id = user.id
        exists = self.db.scalar(
            select(Reaction.id).where(
                Reaction.roast_id == roast_id,
                Reaction.user_id == user_id,
                Reaction.emoji == ReactionEmoji(emoji),
            )
        )
        if exists is None:
            self.db.add(Reaction(roast_id=roast_id, user_id=user_id, emoji=ReactionEmoji(emoji)))
            try:
                self.db.commit()
            except IntegrityError:
                self.db.rollback()
                logger.debug("Reaction race roast=%s user=%s", roast_id, user_id)
        return self.state(roast_id, user)

    def remove_reaction(self, roast_id: int, emoji: str, user: User) -> ReactionState:
        """Remove a reaction; a missing reaction is not an error."""
        self._visible_roast(roast_id, user)
        self.db.execute(
            delete(Reaction).where(
                Reaction.roast_id == roast_id,
                Reaction.user_id == user.id,
                Reaction.emoji == ReactionEmoji(emoji),
            )
        )
        self.db.commit()
        return self.state(roast_id, user)
