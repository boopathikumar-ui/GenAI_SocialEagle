"""Dashboard statistics and bulk settings for the current user."""
import logging
from collections import Counter
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import case, func, select, update
from sqlalchemy.orm import Session

from app.models.reaction import Reaction
from app.models.roast import Roast
from app.schemas.dashboard import (
    DashboardStats,
    DayCount,
    IntensitySplit,
    LanguageCount,
    TopRoast,
    Totals,
)

logger = logging.getLogger(__name__)

SNAPSHOT_SCAN_LIMIT = 500
MAX_LANGUAGES = 8
MAX_TOP_ROASTS = 5


def _as_utc_date(value: datetime) -> date:
    """Normalise a (possibly naive) datetime to a UTC calendar date."""
    if value.tzinfo is None:
        return value.date()
    return value.astimezone(UTC).date()


class DashboardService:
    """Aggregates a single user's roast data."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def stats(self, user_id: int, days: int) -> DashboardStats:
        """Build the dashboard payload for ``user_id``; the series covers ``days`` days."""
        return DashboardStats(
            totals=self._totals(user_id),
            roasts_per_day=self._per_day(user_id, days),
            intensity_split=self._intensity(user_id),
            top_languages=self._languages(user_id),
            top_roasts=self._top_roasts(user_id),
        )

    def _totals(self, user_id: int) -> Totals:
        total, public = self.db.execute(
            select(
                func.count(Roast.id),
                func.coalesce(func.sum(case((Roast.is_public.is_(True), 1), else_=0)), 0),
            ).where(Roast.user_id == user_id)
        ).one()
        reactions = self.db.scalar(
            select(func.count(Reaction.id))
            .join(Roast, Roast.id == Reaction.roast_id)
            .where(Roast.user_id == user_id)
        )
        return Totals(
            roasts=int(total), public_roasts=int(public), reactions_received=int(reactions or 0)
        )

    def _per_day(self, user_id: int, days: int) -> list[DayCount]:
        today = datetime.now(UTC).date()
        start = today - timedelta(days=days - 1)
        start_dt = datetime(start.year, start.month, start.day, tzinfo=UTC)
        rows = self.db.scalars(
            select(Roast.created_at).where(
                Roast.user_id == user_id, Roast.created_at >= start_dt
            )
        ).all()
        counts = Counter(_as_utc_date(r) for r in rows)
        series: list[DayCount] = []
        for i in range(days):
            day = start + timedelta(days=i)
            series.append(DayCount(date=day.isoformat(), count=counts.get(day, 0)))
        return series

    def _intensity(self, user_id: int) -> IntensitySplit:
        rows = self.db.execute(
            select(Roast.intensity, func.count(Roast.id))
            .where(Roast.user_id == user_id)
            .group_by(Roast.intensity)
        ).all()
        split = {"mild": 0, "medium": 0, "spicy": 0}
        for intensity, count in rows:
            split[getattr(intensity, "value", str(intensity))] = int(count)
        return IntensitySplit(**split)

    def _languages(self, user_id: int) -> list[LanguageCount]:
        snapshots = self.db.scalars(
            select(Roast.github_snapshot)
            .where(Roast.user_id == user_id)
            .order_by(Roast.created_at.desc(), Roast.id.desc())
            .limit(SNAPSHOT_SCAN_LIMIT)
        ).all()
        counter: Counter[str] = Counter()
        for snap in snapshots:
            repos = snap.get("top_repos") if isinstance(snap, dict) else None
            if not isinstance(repos, list):
                continue
            for repo in repos:
                lang = repo.get("language") if isinstance(repo, dict) else None
                if isinstance(lang, str) and lang.strip():
                    counter[lang.strip()] += 1
        ranked = sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))[:MAX_LANGUAGES]
        return [LanguageCount(language=k, count=v) for k, v in ranked]

    def _top_roasts(self, user_id: int) -> list[TopRoast]:
        total = func.count(Reaction.id).label("reaction_total")
        rows = self.db.execute(
            select(Roast, total)
            .outerjoin(Reaction, Reaction.roast_id == Roast.id)
            .where(Roast.user_id == user_id)
            .group_by(Roast.id)
            .order_by(total.desc(), Roast.created_at.desc(), Roast.id.desc())
            .limit(MAX_TOP_ROASTS)
        ).all()
        return [
            TopRoast(
                id=r.id,
                github_username=r.github_username,
                intensity=r.intensity.value,  # type: ignore[arg-type]
                share_slug=r.share_slug,
                is_public=r.is_public,
                reaction_total=int(count),
                created_at=r.created_at,
            )
            for r, count in rows
        ]

    def set_all_visibility(self, user_id: int, is_public: bool) -> int:
        """Set ``is_public`` on every roast owned by ``user_id``; return rows updated."""
        result = self.db.execute(
            update(Roast).where(Roast.user_id == user_id).values(is_public=is_public)
        )
        self.db.commit()
        updated = int(getattr(result, "rowcount", 0) or 0)
        logger.info("User %s set %d roasts public=%s", user_id, updated, is_public)
        return updated
