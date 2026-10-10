"""Tests for dashboard stats and settings endpoints."""
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.main import app
from app.models import Intensity, Reaction, ReactionEmoji, Roast, TargetType, User
from app.routers.dashboard import router as dashboard_router
from app.routers.settings import router as settings_router

STATS = "/api/v1/dashboard/stats"
VIS = "/api/v1/settings/roasts-visibility"
RegisterFn = Callable[[str], dict[str, str]]


@pytest.fixture(autouse=True)
def _routers(api: TestClient) -> None:
    """Idempotently include the dashboard/settings routers on the real app."""
    existing = {getattr(r, "path", "") for r in app.routes}
    if f"{settings.API_V1_PREFIX}/dashboard/stats" not in existing:
        app.include_router(dashboard_router, prefix=settings.API_V1_PREFIX)
    if f"{settings.API_V1_PREFIX}/settings/roasts-visibility" not in existing:
        app.include_router(settings_router, prefix=settings.API_V1_PREFIX)


_counter = 0


def make_roast(
    sf: sessionmaker[Session],
    email: str,
    *,
    intensity: Intensity = Intensity.medium,
    is_public: bool = True,
    snapshot: dict[str, Any] | None = None,
    created_at: datetime | None = None,
) -> int:
    """Insert a roast for the user with ``email``."""
    global _counter
    _counter += 1
    with sf() as s:
        user = s.query(User).filter_by(email=email).one()
        roast = Roast(
            user_id=user.id,
            github_url="https://github.com/octocat",
            github_username="octocat",
            target_type=TargetType.profile,
            intensity=intensity,
            roast_text="x",
            github_snapshot=snapshot,
            is_public=is_public,
            share_slug=f"slug{_counter}",
        )
        if created_at is not None:
            roast.created_at = created_at
        s.add(roast)
        s.commit()
        return roast.id


def react(sf: sessionmaker[Session], roast_id: int, emails: list[str]) -> None:
    """Add one reaction per email to the roast, creating reactor users as needed."""
    with sf() as s:
        for i, email in enumerate(emails):
            user = s.query(User).filter_by(email=email).first()
            if user is None:
                user = User(email=email)
                s.add(user)
                s.flush()
            s.add(Reaction(roast_id=roast_id, user_id=user.id, emoji=list(ReactionEmoji)[i % 4]))
        s.commit()


def test_auth_required(api: TestClient) -> None:
    assert api.get(STATS).status_code == 401
    assert api.put(VIS, json={"is_public": False}).status_code == 401


@pytest.mark.parametrize("days", [6, 91, 0])
def test_days_bounds(api: TestClient, register_user: RegisterFn, days: int) -> None:
    h = register_user("a@example.com")
    assert api.get(STATS, params={"days": days}, headers=h).status_code == 422


@pytest.mark.parametrize("days", [7, 30, 90])
def test_zero_filled_series(api: TestClient, register_user: RegisterFn, days: int) -> None:
    h = register_user("a@example.com")
    r = api.get(STATS, params={"days": days}, headers=h)
    assert r.status_code == 200
    series = r.json()["roasts_per_day"]
    assert len(series) == days
    assert all(p["count"] == 0 for p in series)
    dates = [p["date"] for p in series]
    assert dates == sorted(dates)
    assert dates[-1] == datetime.now(UTC).date().isoformat()


def test_default_days_30(api: TestClient, register_user: RegisterFn) -> None:
    h = register_user("a@example.com")
    assert len(api.get(STATS, headers=h).json()["roasts_per_day"]) == 30


def test_totals_split_and_series(
    api: TestClient, register_user: RegisterFn, session_factory: sessionmaker[Session]
) -> None:
    h = register_user("a@example.com")
    now = datetime.now(UTC)
    make_roast(session_factory, "a@example.com", intensity=Intensity.mild)
    make_roast(session_factory, "a@example.com", intensity=Intensity.spicy, is_public=False)
    make_roast(session_factory, "a@example.com", intensity=Intensity.spicy)
    make_roast(session_factory, "a@example.com", created_at=now - timedelta(days=3))
    make_roast(session_factory, "a@example.com", created_at=now - timedelta(days=40))
    body = api.get(STATS, params={"days": 7}, headers=h).json()
    assert body["totals"] == {"roasts": 5, "public_roasts": 4, "reactions_received": 0}
    assert body["intensity_split"] == {"mild": 1, "medium": 2, "spicy": 2}
    series = body["roasts_per_day"]
    assert sum(p["count"] for p in series) == 4  # the 40-day-old roast is outside the window
    assert series[-1]["count"] == 3
    assert series[-4]["count"] == 1


def test_top_languages(
    api: TestClient, register_user: RegisterFn, session_factory: sessionmaker[Session]
) -> None:
    h = register_user("a@example.com")
    langs = ["Python", "Go", "Rust", "C", "Java", "Ruby", "PHP", "Perl", "Lua"]
    make_roast(
        session_factory,
        "a@example.com",
        snapshot={"top_repos": [{"language": x} for x in ["Python", "Python", None, *langs]]},
    )
    make_roast(session_factory, "a@example.com", snapshot={"top_repos": [{"language": "Go"}]})
    make_roast(session_factory, "a@example.com", snapshot=None)
    make_roast(session_factory, "a@example.com", snapshot={"other": 1})
    out = api.get(STATS, headers=h).json()["top_languages"]
    assert len(out) == 8
    assert out[0] == {"language": "Python", "count": 3}
    assert out[1] == {"language": "Go", "count": 2}
    assert all(item["language"] for item in out)


def test_reactions_and_top_roasts(
    api: TestClient, register_user: RegisterFn, session_factory: sessionmaker[Session]
) -> None:
    h = register_user("a@example.com")
    ids = [make_roast(session_factory, "a@example.com") for _ in range(7)]
    react(session_factory, ids[2], ["r1@x.com", "r2@x.com", "r3@x.com"])
    react(session_factory, ids[0], ["r1@x.com"])
    body = api.get(STATS, headers=h).json()
    assert body["totals"]["reactions_received"] == 4
    top = body["top_roasts"]
    assert len(top) == 5
    assert top[0]["id"] == ids[2] and top[0]["reaction_total"] == 3
    assert top[1]["id"] == ids[0] and top[1]["reaction_total"] == 1
    assert top[2]["reaction_total"] == 0
    assert {"share_slug", "is_public", "github_username", "intensity", "created_at"} <= set(top[0])


def test_isolation(
    api: TestClient, register_user: RegisterFn, session_factory: sessionmaker[Session]
) -> None:
    ha = register_user("a@example.com")
    hb = register_user("b@example.com")
    rid = make_roast(
        session_factory, "a@example.com", snapshot={"top_repos": [{"language": "Python"}]}
    )
    react(session_factory, rid, ["b@example.com"])
    b = api.get(STATS, headers=hb).json()
    assert b["totals"] == {"roasts": 0, "public_roasts": 0, "reactions_received": 0}
    assert b["top_roasts"] == [] and b["top_languages"] == []
    assert b["intensity_split"] == {"mild": 0, "medium": 0, "spicy": 0}
    a = api.get(STATS, headers=ha).json()
    assert a["totals"]["roasts"] == 1 and a["totals"]["reactions_received"] == 1


def test_bulk_visibility_only_own(
    api: TestClient, register_user: RegisterFn, session_factory: sessionmaker[Session]
) -> None:
    ha = register_user("a@example.com")
    register_user("b@example.com")
    mine = [make_roast(session_factory, "a@example.com") for _ in range(3)]
    theirs = make_roast(session_factory, "b@example.com")
    r = api.put(VIS, json={"is_public": False}, headers=ha)
    assert r.status_code == 200 and r.json() == {"updated": 3}
    with session_factory() as s:
        for i in mine:
            roast = s.get(Roast, i)
            assert roast is not None and not roast.is_public
        other = s.get(Roast, theirs)
        assert other is not None and other.is_public
    assert api.put(VIS, json={"is_public": True}, headers=ha).json() == {"updated": 3}
    assert api.put(VIS, json={}, headers=ha).status_code == 422


def test_visibility_rate_limit(api: TestClient, register_user: RegisterFn) -> None:
    h = register_user("a@example.com")
    codes = [api.put(VIS, json={"is_public": True}, headers=h).status_code for _ in range(11)]
    assert codes[:10] == [200] * 10 and codes[10] == 429
