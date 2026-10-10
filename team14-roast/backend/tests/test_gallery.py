"""Gallery and reactions tests."""
from collections.abc import Callable, Generator
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.main import app
from app.models.reaction import Reaction, ReactionEmoji
from app.models.roast import Intensity, Roast, TargetType
from app.models.user import User
from app.routers import gallery as gallery_router
from app.routers import reactions as reactions_router

PREFIX = "/api/v1"
RegisterFn = Callable[[str], dict[str, str]]


@pytest.fixture(autouse=True)
def _gallery_routes() -> None:
    """Include the gallery routers on the real app unless already registered."""
    paths = {getattr(r, "path", "") for r in app.routes}
    if f"{PREFIX}/gallery" not in paths:
        app.include_router(gallery_router.router, prefix=PREFIX)
    if f"{PREFIX}/roasts/{{roast_id}}/reactions" not in paths:
        app.include_router(reactions_router.router, prefix=PREFIX)


def _user_id(sf: sessionmaker[Session], email: str) -> int:
    with sf() as s:
        return s.scalars(select(User.id).where(User.email == email)).one()


def _seed_roast(
    sf: sessionmaker[Session],
    n: int,
    user_id: int | None,
    is_public: bool = True,
    age_minutes: int = 0,
) -> int:
    with sf() as s:
        roast = Roast(
            user_id=user_id,
            github_url=f"https://github.com/secret{n}",
            github_username=f"user{n}",
            target_type=TargetType.profile,
            intensity=Intensity.medium,
            roast_text=f"roast {n}",
            github_snapshot={"private": "snapshot"},
            is_public=is_public,
            share_slug=f"slug{n:04d}",
            created_at=datetime.now(UTC) - timedelta(minutes=age_minutes),
        )
        s.add(roast)
        s.commit()
        return roast.id


def _react(api: TestClient, headers: dict[str, str], roast_id: int, emoji: str) -> Any:
    return api.post(f"{PREFIX}/roasts/{roast_id}/reactions", json={"emoji": emoji}, headers=headers)


def test_public_only_and_no_leakage(
    api: TestClient, session_factory: sessionmaker[Session], register_user: RegisterFn
) -> None:
    register_user("a@example.com")
    uid = _user_id(session_factory, "a@example.com")
    pub = _seed_roast(session_factory, 1, uid)
    _seed_roast(session_factory, 2, uid, is_public=False)
    body = api.get(f"{PREFIX}/gallery").json()
    assert body["total"] == 1
    assert [i["id"] for i in body["items"]] == [pub]
    item = body["items"][0]
    assert set(item) == {
        "id", "github_username", "target_type", "intensity", "roast_text",
        "share_slug", "created_at", "reaction_counts", "my_reactions",
    }  # fmt: skip
    assert item["reaction_counts"] == {"fire": 0, "skull": 0, "laugh": 0, "clap": 0}
    assert item["my_reactions"] == []
    assert "snapshot" not in api.get(f"{PREFIX}/gallery").text
    assert "secret1" not in api.get(f"{PREFIX}/gallery").text


def test_pagination_bounds_and_order(
    api: TestClient, session_factory: sessionmaker[Session], register_user: RegisterFn
) -> None:
    register_user("a@example.com")
    uid = _user_id(session_factory, "a@example.com")
    ids = [_seed_roast(session_factory, i, uid, age_minutes=i) for i in range(5)]
    r = api.get(f"{PREFIX}/gallery", params={"page": 2, "page_size": 2}).json()
    assert r["total"] == 5 and r["page"] == 2 and r["page_size"] == 2
    assert [i["id"] for i in r["items"]] == [ids[2], ids[3]]
    assert api.get(f"{PREFIX}/gallery", params={"page": 9}).json()["items"] == []
    for params in ({"page_size": 0}, {"page_size": 51}, {"page": 0}, {"sort": "bogus"}):
        assert api.get(f"{PREFIX}/gallery", params=params).status_code == 422
    assert api.get(f"{PREFIX}/gallery", params={"page_size": 50}).status_code == 200


def test_sort_top_and_counts(
    api: TestClient, session_factory: sessionmaker[Session], register_user: RegisterFn
) -> None:
    ha = register_user("a@example.com")
    hb = register_user("b@example.com")
    uid = _user_id(session_factory, "a@example.com")
    newest = _seed_roast(session_factory, 1, uid, age_minutes=0)
    popular = _seed_roast(session_factory, 2, uid, age_minutes=10)
    mid = _seed_roast(session_factory, 3, uid, age_minutes=5)
    _react(api, ha, popular, "fire")
    _react(api, hb, popular, "fire")
    _react(api, hb, popular, "skull")
    _react(api, ha, mid, "clap")
    top = api.get(f"{PREFIX}/gallery", params={"sort": "top"}, headers=ha).json()["items"]
    assert [i["id"] for i in top] == [popular, mid, newest]
    assert top[0]["reaction_counts"] == {"fire": 2, "skull": 1, "laugh": 0, "clap": 0}
    assert top[0]["my_reactions"] == ["fire"]
    anon = api.get(f"{PREFIX}/gallery", params={"sort": "top"}).json()["items"]
    assert all(i["my_reactions"] == [] for i in anon)
    new = api.get(f"{PREFIX}/gallery", params={"sort": "new"}).json()["items"]
    assert [i["id"] for i in new] == [newest, mid, popular]


def test_add_remove_idempotent(
    api: TestClient, session_factory: sessionmaker[Session], register_user: RegisterFn
) -> None:
    h = register_user("a@example.com")
    rid = _seed_roast(session_factory, 1, _user_id(session_factory, "a@example.com"))
    first = _react(api, h, rid, "fire")
    assert first.status_code == 200
    assert first.json() == {
        "reaction_counts": {"fire": 1, "skull": 0, "laugh": 0, "clap": 0},
        "my_reactions": ["fire"],
    }
    assert _react(api, h, rid, "fire").json() == first.json()
    with session_factory() as s:
        assert len(s.scalars(select(Reaction)).all()) == 1
    d = api.delete(f"{PREFIX}/roasts/{rid}/reactions/fire", headers=h)
    assert d.status_code == 200
    assert d.json()["my_reactions"] == [] and d.json()["reaction_counts"]["fire"] == 0
    assert api.delete(f"{PREFIX}/roasts/{rid}/reactions/fire", headers=h).status_code == 200
    assert api.delete(f"{PREFIX}/roasts/{rid}/reactions/nope", headers=h).status_code == 422
    assert _react(api, h, rid, "nope").status_code == 422


def test_private_and_auth_rules(
    api: TestClient, session_factory: sessionmaker[Session], register_user: RegisterFn
) -> None:
    ha = register_user("a@example.com")
    hb = register_user("b@example.com")
    priv = _seed_roast(session_factory, 1, _user_id(session_factory, "a@example.com"), False)
    assert _react(api, hb, priv, "fire").status_code == 404
    assert api.delete(f"{PREFIX}/roasts/{priv}/reactions/fire", headers=hb).status_code == 404
    assert _react(api, ha, priv, "fire").status_code == 200  # owner may react
    assert _react(api, hb, 99999, "fire").status_code == 404
    assert api.post(f"{PREFIX}/roasts/{priv}/reactions", json={"emoji": "fire"}).status_code == 401
    assert api.delete(f"{PREFIX}/roasts/{priv}/reactions/fire").status_code == 401
    assert api.get(f"{PREFIX}/gallery").json()["total"] == 0


def test_reactions_do_not_shadow_roast_routes(
    api: TestClient, session_factory: sessionmaker[Session], register_user: RegisterFn
) -> None:
    h = register_user("a@example.com")
    rid = _seed_roast(session_factory, 1, _user_id(session_factory, "a@example.com"))
    assert api.get(f"{PREFIX}/roasts/{rid}", headers=h).status_code == 200


def test_rate_limit_reactions(
    api: TestClient, session_factory: sessionmaker[Session], register_user: RegisterFn
) -> None:
    h = register_user("a@example.com")
    rid = _seed_roast(session_factory, 1, _user_id(session_factory, "a@example.com"))
    codes = [_react(api, h, rid, "fire").status_code for _ in range(61)]
    assert codes[:60] == [200] * 60 and codes[60] == 429


@pytest.fixture()
def query_counter(session_factory: sessionmaker[Session]) -> Generator[list[str], None, None]:
    engine = session_factory.kw["bind"]
    assert isinstance(engine, Engine)
    statements: list[str] = []

    def _count(conn: Any, cursor: Any, statement: str, *args: Any) -> None:
        statements.append(statement)

    event.listen(engine, "before_cursor_execute", _count)
    yield statements
    event.remove(engine, "before_cursor_execute", _count)


@pytest.mark.parametrize("sort", ["new", "top"])
def test_no_n_plus_one(
    api: TestClient,
    session_factory: sessionmaker[Session],
    register_user: RegisterFn,
    query_counter: list[str],
    sort: str,
) -> None:
    h = register_user("a@example.com")
    uid = _user_id(session_factory, "a@example.com")
    ids = [_seed_roast(session_factory, i, uid, age_minutes=i) for i in range(30)]
    with session_factory() as s:
        for rid in ids:
            s.add(Reaction(roast_id=rid, user_id=uid, emoji=ReactionEmoji.fire))
        s.commit()

    def count(page_size: int) -> int:
        query_counter.clear()
        r = api.get(f"{PREFIX}/gallery", params={"page_size": page_size, "sort": sort}, headers=h)
        assert r.status_code == 200 and len(r.json()["items"]) == page_size
        return len(query_counter)

    assert count(1) == count(5) == count(30)
