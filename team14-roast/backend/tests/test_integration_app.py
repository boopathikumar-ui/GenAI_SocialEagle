"""Integration tests through the real app.main app."""
from typing import Any

from urllib.parse import parse_qs, urlparse

import httpx
import pytest
from anthropic import APIConnectionError
from fastapi.testclient import TestClient

from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.models.user import User
from app.services import auth_service
from tests.conftest import AUTH, ROASTS, FakeLLM, RegisterFn


def _create(api: TestClient, headers: dict[str, str] | None = None, **over: Any) -> Any:
    body = {"github_url": "https://github.com/octocat", "intensity": "spicy", **over}
    return api.post(ROASTS, json=body, headers=headers or {})


def test_health(api: TestClient) -> None:
    assert api.get("/health").json() == {"status": "ok"}


def test_auth_flow(api: TestClient) -> None:
    body = {"email": "Bob@Example.com", "password": "supersecret1", "full_name": "Bob"}
    r = api.post(f"{AUTH}/register", json=body)
    assert r.status_code == 201
    assert r.json()["user"]["email"] == "bob@example.com"
    assert api.post(f"{AUTH}/register", json=body).status_code == 409
    assert api.post(f"{AUTH}/register", json={**body, "password": "short"}).status_code == 422

    bad = api.post(f"{AUTH}/login", json={"email": "bob@example.com", "password": "nope-nope1"})
    assert bad.status_code == 401
    tokens = api.post(
        f"{AUTH}/login", json={"email": "bob@example.com", "password": "supersecret1"}
    ).json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    assert api.get(f"{AUTH}/me", headers=headers).json()["full_name"] == "Bob"
    assert api.get(f"{AUTH}/me").status_code == 401
    assert api.get(f"{AUTH}/me", headers={"Authorization": "Bearer junk"}).status_code == 401
    refresh_h = {"Authorization": f"Bearer {tokens['refresh_token']}"}
    assert api.get(f"{AUTH}/me", headers=refresh_h).status_code == 401
    updated = api.put(f"{AUTH}/me", headers=headers, json={"full_name": "Bobby"})
    assert updated.json()["full_name"] == "Bobby"

    rotated = api.post(f"{AUTH}/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert rotated.status_code == 200
    # old refresh token is single-use
    reuse = api.post(f"{AUTH}/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert reuse.status_code == 401
    new_refresh = rotated.json()["refresh_token"]
    assert api.post(f"{AUTH}/logout", json={"refresh_token": new_refresh}).status_code == 204
    assert api.post(f"{AUTH}/refresh", json={"refresh_token": new_refresh}).status_code == 401
    assert api.post(f"{AUTH}/refresh", json={"refresh_token": "garbage"}).status_code == 401


def test_login_rate_limited(api: TestClient) -> None:
    payload = {"email": "x@example.com", "password": "wrongpass12"}
    codes = [api.post(f"{AUTH}/login", json=payload).status_code for _ in range(12)]
    assert codes[:10] == [401] * 10
    assert 429 in codes[10:]


def test_google_not_configured(api: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "")
    assert api.get(f"{AUTH}/google", follow_redirects=False).status_code == 502


def _assert_oauth_failed(resp: httpx.Response) -> None:
    assert resp.status_code == 302
    assert resp.headers["location"].endswith("/login?error=oauth_failed")


def test_google_bad_callback(api: TestClient) -> None:
    _assert_oauth_failed(api.get(f"{AUTH}/google/callback?code=x&state=y", follow_redirects=False))
    _assert_oauth_failed(api.get(f"{AUTH}/google/callback?error=access_denied", follow_redirects=False))
    forged = {"Cookie": "oauth_state=not-a-jwt"}
    _assert_oauth_failed(
        api.get(f"{AUTH}/google/callback?code=x&state=y", headers=forged, follow_redirects=False)
    )


def _google_state(api: TestClient) -> tuple[str, str]:
    r = api.get(f"{AUTH}/google", follow_redirects=False)
    assert r.status_code in (302, 307)
    state = parse_qs(urlparse(r.headers["location"]).query)["state"][0]
    cookie = r.headers["set-cookie"].split(";")[0]
    return state, cookie


def test_google_flow(api: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "cid")
    profile: dict[str, object] = {"email": "G@Example.com", "name": "Gee", "email_verified": True}

    async def fake_profile(code: str, redirect_uri: str) -> dict[str, object]:
        return profile

    monkeypatch.setattr(auth_service, "google_fetch_profile", fake_profile)
    state, cookie = _google_state(api)
    # mismatched state is rejected
    bad = api.get(
        f"{AUTH}/google/callback?code=c&state=zzz",
        headers={"Cookie": cookie},
        follow_redirects=False,
    )
    _assert_oauth_failed(bad)
    ok = api.get(
        f"{AUTH}/google/callback?code=c&state={state}",
        headers={"Cookie": cookie},
        follow_redirects=False,
    )
    assert ok.status_code in (302, 307)
    # tokens travel in the URL fragment, never the query string
    assert "/auth/callback#access_token=" in ok.headers["location"]
    assert "?access_token=" not in ok.headers["location"]
    # second login reuses the same user
    ok2 = api.get(
        f"{AUTH}/google/callback?code=c&state={state}",
        headers={"Cookie": cookie},
        follow_redirects=False,
    )
    assert ok2.status_code in (302, 307)
    # unverified Google email is rejected
    profile["email_verified"] = False
    rej = api.get(
        f"{AUTH}/google/callback?code=c&state={state}",
        headers={"Cookie": cookie},
        follow_redirects=False,
    )
    _assert_oauth_failed(rej)


def test_register_then_google_links_existing_user(
    api: TestClient, db: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    api.post(f"{AUTH}/register", json={"email": "p@example.com", "password": "supersecret1", "full_name": "P"})
    user = auth_service.upsert_google_user(
        db, {"email": "p@example.com", "name": "P", "email_verified": True}
    )
    # linking invalidates the pre-existing password (account pre-hijacking defense)
    assert user.is_verified and user.hashed_password is None
    assert api.post(
        f"{AUTH}/login", json={"email": "p@example.com", "password": "supersecret1"}
    ).status_code == 401


def test_disabled_user_cannot_login(api: TestClient, session_factory: sessionmaker[Session]) -> None:
    body = {"email": "d@example.com", "password": "supersecret1"}
    reg = api.post(f"{AUTH}/register", json={**body, "full_name": "D"})
    assert reg.status_code == 201
    with session_factory() as s:
        s.query(User).filter_by(email="d@example.com").update({"is_active": False})
        s.commit()
    assert api.post(f"{AUTH}/login", json=body).status_code == 403


def test_roast_crud_flow(api: TestClient, register_user: RegisterFn, fake_llm: FakeLLM) -> None:
    h = register_user()
    r = _create(api, h)
    assert r.status_code == 201, r.text
    data = r.json()
    assert "github_snapshot" not in data
    assert data["target_type"] == "profile" and data["user_id"] is not None
    assert "<github_data>" in fake_llm.calls[0]["messages"][0]["content"]

    rid, slug = data["id"], data["share_slug"]
    assert api.get(f"{ROASTS}/{rid}", headers=h).json()["id"] == rid
    lst = api.get(f"{ROASTS}?page=1&page_size=5", headers=h).json()
    assert lst["total"] == 1 and lst["items"][0]["id"] == rid
    # roasts are private by default: the share link does not resolve until made public
    assert data["is_public"] is False
    assert api.get(f"{ROASTS}/s/{slug}").status_code == 404
    made_public = api.patch(f"{ROASTS}/{rid}", json={"is_public": True}, headers=h)
    assert made_public.json()["is_public"] is True
    assert api.get(f"{ROASTS}/s/{slug}").status_code == 200  # no auth needed

    patched = api.patch(f"{ROASTS}/{rid}", json={"is_public": False}, headers=h)
    assert patched.json()["is_public"] is False
    assert api.get(f"{ROASTS}/s/{slug}").status_code == 404
    assert api.get(f"{ROASTS}/s/nope").status_code == 404

    assert api.delete(f"{ROASTS}/{rid}", headers=h).status_code == 204
    assert api.get(f"{ROASTS}/{rid}", headers=h).status_code == 404


def test_repo_target_and_private_create(api: TestClient, register_user: RegisterFn) -> None:
    h = register_user()
    r = _create(api, h, github_url="https://github.com/octocat/Hello-World", is_public=False)
    assert r.status_code == 201
    assert r.json()["target_type"] == "repo"
    assert api.get(f"{ROASTS}/s/{r.json()['share_slug']}").status_code == 404


def test_github_upstream_error(api: TestClient) -> None:
    assert _create(api, github_url="https://github.com/boom").status_code == 502


def test_list_pagination_and_validation(api: TestClient, register_user: RegisterFn) -> None:
    h = register_user()
    for _ in range(3):
        assert _create(api, h).status_code == 201
    page = api.get(f"{ROASTS}?page=2&page_size=2", headers=h).json()
    assert page["total"] == 3 and len(page["items"]) == 1
    assert api.get(f"{ROASTS}?page=0", headers=h).status_code == 422
    assert api.get(f"{ROASTS}?page_size=51", headers=h).status_code == 422


def test_ownership_isolation(api: TestClient, register_user: RegisterFn) -> None:
    a = register_user("a@example.com")
    b = register_user("b@example.com")
    rid = _create(api, a).json()["id"]
    assert api.get(f"{ROASTS}/{rid}", headers=b).status_code == 404
    assert api.delete(f"{ROASTS}/{rid}", headers=b).status_code == 404
    assert api.patch(f"{ROASTS}/{rid}", json={"is_public": False}, headers=b).status_code == 404
    assert api.get(ROASTS, headers=b).json()["total"] == 0
    assert api.get(f"{ROASTS}/{rid}", headers=a).status_code == 200


def test_unauthenticated_access_rejected(api: TestClient, register_user: RegisterFn) -> None:
    rid = _create(api, register_user()).json()["id"]
    assert api.get(ROASTS).status_code == 401
    assert api.get(f"{ROASTS}/{rid}").status_code == 401
    assert api.delete(f"{ROASTS}/{rid}").status_code == 401
    assert api.patch(f"{ROASTS}/{rid}", json={"is_public": False}).status_code == 401


def test_anonymous_create(api: TestClient) -> None:
    r = _create(api)
    assert r.status_code == 201
    assert r.json()["user_id"] is None
    # an invalid token on an optional-auth route degrades to anonymous
    r2 = _create(api, {"Authorization": "Bearer junk"})
    assert r2.status_code == 201 and r2.json()["user_id"] is None


def test_roast_bad_inputs(api: TestClient) -> None:
    assert _create(api, github_url="https://github.com.evil.com/x").status_code == 422
    assert _create(api, intensity="nuclear").status_code == 422
    assert _create(api, github_url="https://github.com/ghost").status_code == 404
    assert _create(api, github_url="https://github.com/limited").status_code == 429


def test_roast_create_rate_limited(api: TestClient) -> None:
    codes = [_create(api).status_code for _ in range(7)]
    assert codes[:5] == [201] * 5
    assert 429 in codes[5:]


def test_llm_failure_is_friendly(api: TestClient, fake_llm: FakeLLM) -> None:
    fake_llm.outputs = APIConnectionError(request=httpx.Request("POST", "https://x"))
    r = _create(api)
    assert r.status_code >= 500
    assert "Traceback" not in r.text
