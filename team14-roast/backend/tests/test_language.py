"""Roast language option (English / Thanglish). All LLMs are mocked."""
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.services.fake_roaster import fake_roast
from app.services.roast_service import build_user_prompt, contains_blocked_term
from tests.conftest import ROASTS, FakeLLM

SNAPSHOT: dict[str, Any] = {
    "target_type": "profile",
    "profile": {"login": "octocat"},
    "top_repos": [{"name": "hello-world", "language": "Python", "stars": 12}],
    "recent_commits": ["fix stuff"],
    "readme_snippet": "",
}


def test_english_prompt_has_no_language_instruction() -> None:
    assert "Thanglish" not in build_user_prompt(SNAPSHOT, "mild")
    assert "Thanglish" not in build_user_prompt(SNAPSHOT, "mild", "english")


def test_thanglish_prompt_asks_for_latin_script_and_family_friendly() -> None:
    prompt = build_user_prompt(SNAPSHOT, "spicy", "thanglish")
    assert "Thanglish" in prompt
    assert "Do NOT use Tamil script" in prompt
    assert "no abusive words" in prompt
    # the untrusted-data delimiter and the safety rules are still in place
    assert "<github_data>" in prompt


def test_unknown_language_falls_back_to_english_prompt() -> None:
    assert build_user_prompt(SNAPSHOT, "mild", "klingon") == build_user_prompt(SNAPSHOT, "mild")


@pytest.mark.parametrize("intensity", ["mild", "medium", "spicy"])
def test_fake_thanglish_differs_from_english_and_is_clean(intensity: str) -> None:
    english = fake_roast(SNAPSHOT, intensity, "english")
    thanglish = fake_roast(SNAPSHOT, intensity, "thanglish")
    assert thanglish != english
    assert thanglish == fake_roast(SNAPSHOT, intensity, "thanglish")  # deterministic
    assert "octocat" in thanglish and "hello-world" in thanglish
    assert not contains_blocked_term(thanglish)
    assert thanglish.isascii()  # Latin letters only, no Tamil script


def test_api_defaults_to_english(api: TestClient, fake_llm: FakeLLM) -> None:
    r = api.post(ROASTS, json={"github_url": "https://github.com/octocat", "intensity": "mild"})
    assert r.status_code == 201
    assert "Thanglish" not in fake_llm.calls[0]["messages"][0]["content"]


def test_api_passes_thanglish_to_the_model(api: TestClient, fake_llm: FakeLLM) -> None:
    r = api.post(
        ROASTS,
        json={"github_url": "https://github.com/octocat", "intensity": "mild", "language": "thanglish"},
    )
    assert r.status_code == 201, r.text
    assert "Thanglish" in fake_llm.calls[0]["messages"][0]["content"]


def test_api_rejects_unknown_language(api: TestClient) -> None:
    r = api.post(
        ROASTS,
        json={"github_url": "https://github.com/octocat", "intensity": "mild", "language": "klingon"},
    )
    assert r.status_code == 422
