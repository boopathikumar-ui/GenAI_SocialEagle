"""Smoke test for the auth module (register/login/refresh/me/logout)."""
import os
from collections.abc import Generator

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "test-secret-key-test-secret-key-0123456789")

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import get_db
from app.exceptions import register_exception_handlers
from app.models import Base
from app.rate_limit import limiter
from app.routers.auth import router

PREFIX = "/api/v1/auth"


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    """TestClient on an app with only the auth router and an in-memory DB."""
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False)

    def override_db() -> Generator[Session, None, None]:
        db = factory()
        try:
            yield db
        finally:
            db.close()

    app = FastAPI()
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]
    register_exception_handlers(app)
    app.include_router(router, prefix="/api/v1")
    app.dependency_overrides[get_db] = override_db
    limiter.reset()
    with TestClient(app) as test_client:
        yield test_client


def test_auth_flow(client: TestClient) -> None:
    """Exercise the full auth lifecycle."""
    body = {"email": "A@Example.com", "password": "supersecret1", "full_name": "Ann"}
    r = client.post(f"{PREFIX}/register", json=body)
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "a@example.com"
    assert "hashed_password" not in data["user"]

    assert client.post(f"{PREFIX}/register", json=body).status_code == 409
    bad = client.post(f"{PREFIX}/login", json={"email": "a@example.com", "password": "wrongpass1"})
    assert bad.status_code == 401

    r = client.post(f"{PREFIX}/login", json={"email": "a@example.com", "password": "supersecret1"})
    assert r.status_code == 200
    tokens = r.json()

    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    assert client.get(f"{PREFIX}/me", headers=headers).json()["full_name"] == "Ann"
    assert client.get(f"{PREFIX}/me").status_code == 401
    # refresh token is not usable as an access token
    refresh_headers = {"Authorization": f"Bearer {tokens['refresh_token']}"}
    assert client.get(f"{PREFIX}/me", headers=refresh_headers).status_code == 401

    r = client.put(f"{PREFIX}/me", headers=headers, json={"full_name": "Anne"})
    assert r.json()["full_name"] == "Anne"

    r = client.post(f"{PREFIX}/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert r.status_code == 200
    new = r.json()
    assert new["refresh_token"] != tokens["refresh_token"]
    # old refresh token revoked
    r = client.post(f"{PREFIX}/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert r.status_code == 401

    r = client.post(f"{PREFIX}/logout", json={"refresh_token": new["refresh_token"]})
    assert r.status_code == 204
    r = client.post(f"{PREFIX}/refresh", json={"refresh_token": new["refresh_token"]})
    assert r.status_code == 401


def test_google_state_rejected(client: TestClient) -> None:
    """Callback without matching state cookie is rejected."""
    r = client.get(
        f"{PREFIX}/google/callback",
        params={"code": "x", "state": "y"},
        follow_redirects=False,
    )
    assert r.status_code == 302
    assert r.headers["location"].endswith("/login?error=oauth_failed")
