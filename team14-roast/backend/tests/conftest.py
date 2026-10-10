"""Shared fixtures: in-memory DB, real app client, mocked GitHub and Anthropic."""
import base64
import os
from collections.abc import Callable, Generator
from types import SimpleNamespace
from typing import Any

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "test-secret-key-test-secret-key-0123456789")

import httpx  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.database import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Base  # noqa: E402
from app.rate_limit import limiter  # noqa: E402
from app.routers import roasts as roasts_router  # noqa: E402
from app.services.github_service import GitHubService  # noqa: E402
from app.services.roast_service import RoastService  # noqa: E402

AUTH = "/api/v1/auth"
ROASTS = "/api/v1/roasts"


def github_handler(request: httpx.Request) -> httpx.Response:
    """Fake api.github.com; any non-GitHub host fails the test."""
    assert request.url.host == "api.github.com", f"unexpected host {request.url.host}"
    path = request.url.path
    if path in ("/users/octocat", "/users/other"):
        name = path.rsplit("/", 1)[1]
        return httpx.Response(
            200, json={"login": name, "name": "Octo", "bio": "hi", "followers": 5, "public_repos": 2}
        )
    if path in ("/users/octocat/repos", "/users/other/repos"):
        return httpx.Response(
            200,
            json=[
                {"name": "a", "language": "Python", "stargazers_count": 1, "description": "d"},
                {"name": "b", "language": "Go", "stargazers_count": 9, "description": None},
            ],
        )
    if path == "/repos/octocat/Hello-World":
        return httpx.Response(200, json={"name": "Hello-World", "language": "C", "stargazers_count": 3})
    if path == "/users/boom":
        return httpx.Response(500, json={})
    if path.endswith("/commits"):
        return httpx.Response(200, json=[{"commit": {"message": "fix stuff\n\nbody"}}])
    if path.endswith("/readme"):
        content = base64.b64encode(b"# hello").decode()
        return httpx.Response(200, json={"encoding": "base64", "content": content})
    if path == "/users/limited":
        return httpx.Response(403, json={"message": "API rate limit exceeded"})
    return httpx.Response(404, json={})


class FakeLLM:
    """Stand-in for AsyncAnthropic. Never touches the network."""

    def __init__(self, outputs: list[str] | Exception | None = None) -> None:
        self.outputs = outputs if outputs is not None else ["A museum of TODOs. " * 5] * 200
        self.calls: list[dict[str, Any]] = []
        self.messages = self

    async def create(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        if isinstance(self.outputs, Exception):
            raise self.outputs
        return SimpleNamespace(content=[SimpleNamespace(text=self.outputs.pop(0))])


@pytest.fixture()
def session_factory() -> sessionmaker[Session]:
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False)


@pytest.fixture()
def db(session_factory: sessionmaker[Session]) -> Generator[Session, None, None]:
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def github_service() -> GitHubService:
    return GitHubService(httpx.AsyncClient(transport=httpx.MockTransport(github_handler)))


@pytest.fixture()
def fake_llm() -> FakeLLM:
    return FakeLLM()


@pytest.fixture()
def api(
    session_factory: sessionmaker[Session],
    github_service: GitHubService,
    fake_llm: FakeLLM,
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[TestClient, None, None]:
    """TestClient on the real app.main app with mocked externals and a fresh limiter."""

    def make_service(session: Session) -> RoastService:
        return RoastService(session, github=github_service, llm=fake_llm)  # type: ignore[arg-type]

    monkeypatch.setattr(roasts_router, "RoastService", make_service)

    def override_db() -> Generator[Session, None, None]:
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_db
    limiter.reset()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    limiter.reset()


RegisterFn = Callable[[str], dict[str, str]]


@pytest.fixture()
def register_user(api: TestClient) -> RegisterFn:
    """Register a user and return Authorization headers."""

    def _register(email: str = "a@example.com") -> dict[str, str]:
        r = api.post(
            f"{AUTH}/register",
            json={"email": email, "password": "supersecret1", "full_name": "Test"},
        )
        assert r.status_code == 201, r.text
        return {"Authorization": f"Bearer {r.json()['access_token']}"}

    return _register
