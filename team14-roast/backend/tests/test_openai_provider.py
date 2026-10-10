"""OpenAI provider tests. The OpenAI client is always mocked; no network is used."""
from types import SimpleNamespace
from typing import Any

import httpx
import openai
import pytest
from sqlalchemy.orm import Session

from app.config import Settings, settings
from app.exceptions import ExternalServiceError, ServiceUnavailableError
from app.services import roast_service
from app.services.roast_service import FALLBACK_TEXT, RoastService

SNAPSHOT: dict[str, Any] = {
    "target_type": "profile",
    "profile": {"login": "octocat"},
    "top_repos": [{"name": "hello-world", "language": "Python", "stars": 1}],
}


def _completion(text: str | None, finish: str = "stop") -> SimpleNamespace:
    msg = SimpleNamespace(content=text)
    return SimpleNamespace(choices=[SimpleNamespace(message=msg, finish_reason=finish)])


class FakeOpenAI:
    """Stand-in for AsyncOpenAI: replays queued results/exceptions, records calls."""

    def __init__(self, *results: Any) -> None:
        self.results = list(results)
        self.calls: list[dict[str, Any]] = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    async def _create(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        result = self.results.pop(0)
        if isinstance(result, BaseException):
            raise result
        return result


def _response(status: int) -> httpx.Response:
    return httpx.Response(status, request=httpx.Request("POST", "https://api.openai.com/v1/x"))


@pytest.fixture(autouse=True)
def _openai_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "ROAST_PROVIDER", "openai")
    monkeypatch.setattr(settings, "OPENAI_ROAST_MODEL", "test-model")


def _service(db: Session, client: FakeOpenAI) -> RoastService:
    return RoastService(db, openai_client=client)  # type: ignore[arg-type]


def test_provider_can_be_set_to_openai() -> None:
    s = Settings(  # type: ignore[call-arg]
        _env_file=None, DATABASE_URL="sqlite://", SECRET_KEY="k" * 40, ROAST_PROVIDER="openai"
    )
    assert s.ROAST_PROVIDER == "openai" and s.OPENAI_ROAST_MODEL


def test_unknown_provider_rejected() -> None:
    with pytest.raises(ValueError):
        Settings(  # type: ignore[call-arg]
            _env_file=None, DATABASE_URL="sqlite://", SECRET_KEY="k" * 40, ROAST_PROVIDER="nope"
        )


@pytest.mark.asyncio
async def test_openai_roast_uses_safe_prompt_and_model(db: Session) -> None:
    client = FakeOpenAI(_completion("octocat writes tests like unicorns exist."))
    text = await _service(db, client).generate_text(SNAPSHOT, "mild")
    assert text.startswith("octocat")
    call = client.calls[0]
    assert call["model"] == "test-model"
    system, user = call["messages"]
    assert system["role"] == "system" and "IGNORE" in system["content"]
    assert user["role"] == "user" and "<github_data>" in user["content"]


@pytest.mark.asyncio
async def test_openai_blocked_output_retries_then_falls_back(db: Session) -> None:
    client = FakeOpenAI(_completion("you should kill yourself"), _completion("kys"))
    text = await _service(db, client).generate_text(SNAPSHOT, "spicy")
    assert text == FALLBACK_TEXT
    assert len(client.calls) == 2


@pytest.mark.asyncio
async def test_openai_truncated_output_is_not_stored(db: Session) -> None:
    client = FakeOpenAI(_completion("cut off mid", "length"), _completion("cut again", "length"))
    with pytest.raises(ExternalServiceError):
        await _service(db, client).generate_text(SNAPSHOT, "medium")


@pytest.mark.asyncio
async def test_openai_empty_output_is_an_error(db: Session) -> None:
    with pytest.raises(ExternalServiceError):
        await _service(db, FakeOpenAI(_completion(None))).generate_text(SNAPSHOT, "mild")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (openai.AuthenticationError("bad key", response=_response(401), body=None), ServiceUnavailableError),
        (openai.RateLimitError("quota", response=_response(429), body=None), ServiceUnavailableError),
        (openai.APIConnectionError(request=httpx.Request("POST", "https://x")), ExternalServiceError),
    ],
)
async def test_openai_errors_become_friendly_errors(
    db: Session, error: Exception, expected: type[Exception]
) -> None:
    with pytest.raises(expected):
        await _service(db, FakeOpenAI(error)).generate_text(SNAPSHOT, "mild")


@pytest.mark.asyncio
async def test_missing_openai_key_is_503_not_a_crash(
    db: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "")
    monkeypatch.setattr(roast_service, "_openai_singleton", None)
    with pytest.raises(ServiceUnavailableError):
        await RoastService(db).generate_text(SNAPSHOT, "mild")


@pytest.mark.asyncio
async def test_openai_provider_never_creates_claude_client(
    db: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    def boom() -> None:
        raise AssertionError("Anthropic client must not be used for ROAST_PROVIDER=openai")

    monkeypatch.setattr(roast_service, "get_llm_client", boom)
    text = await _service(db, FakeOpenAI(_completion("fine."))).generate_text(SNAPSHOT, "mild")
    assert text == "fine."
