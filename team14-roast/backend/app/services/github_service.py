"""GitHub URL validation and public-data snapshot fetching."""
import asyncio
import base64
import logging
import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit

import httpx

from app.config import settings
from app.exceptions import ExternalServiceError, NotFoundError, RateLimitError, ValidationError

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"
ALLOWED_HOSTS = {"github.com", "www.github.com"}
USERNAME_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?$")
REPO_RE = re.compile(r"^[A-Za-z0-9._-]{1,100}$")
README_MAX_CHARS = 1500
FIELD_MAX_CHARS = 300
INVALID_URL_MSG = (
    "Please enter a valid GitHub profile or repository URL "
    "(https://github.com/user or https://github.com/user/repo)."
)


@dataclass(frozen=True)
class GitHubTarget:
    username: str
    repo: str | None
    canonical_url: str

    @property
    def target_type(self) -> str:
        return "repo" if self.repo else "profile"


def parse_github_url(url: str) -> GitHubTarget:
    """Strictly validate a GitHub URL (SSRF prevention). Raises ValidationError."""
    if not isinstance(url, str):
        raise ValidationError(INVALID_URL_MSG)
    raw = url.strip()
    if not raw or len(raw) > 300 or any(ord(c) < 33 or ord(c) > 126 for c in raw):
        raise ValidationError(INVALID_URL_MSG)
    if "\\" in raw or "@" in raw or "%" in raw:
        raise ValidationError(INVALID_URL_MSG)
    try:
        parts = urlsplit(raw)
        port = parts.port
    except ValueError:
        raise ValidationError(INVALID_URL_MSG) from None
    if parts.scheme != "https" or port is not None or parts.username or parts.password:
        raise ValidationError(INVALID_URL_MSG)
    if parts.netloc.lower() not in ALLOWED_HOSTS or parts.query or parts.fragment:
        raise ValidationError(INVALID_URL_MSG)
    stripped = parts.path.strip("/")
    segments = stripped.split("/") if stripped else []
    if "//" in parts.path.rstrip("/") or not 1 <= len(segments) <= 2:
        raise ValidationError(INVALID_URL_MSG)
    username = segments[0]
    if not USERNAME_RE.fullmatch(username) or "--" in username:
        raise ValidationError(INVALID_URL_MSG)
    repo: str | None = None
    if len(segments) == 2:
        repo = segments[1]
        if repo.endswith(".git"):
            repo = repo[:-4]
        if repo in {".", ".."} or not REPO_RE.fullmatch(repo):
            raise ValidationError(INVALID_URL_MSG)
    canonical = f"https://github.com/{username}" + (f"/{repo}" if repo else "")
    return GitHubTarget(username=username, repo=repo, canonical_url=canonical)


def _clip(value: Any, limit: int = FIELD_MAX_CHARS) -> str | None:
    if value is None:
        return None
    return str(value)[:limit]


class GitHubService:
    """Fetches public data from api.github.com only."""

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "team14-roast",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if settings.GITHUB_TOKEN:
            headers["Authorization"] = f"Bearer {settings.GITHUB_TOKEN}"
        return headers

    async def _get(
        self, client: httpx.AsyncClient, path: str, params: dict[str, Any] | None = None
    ) -> Any:
        try:
            resp = await client.get(f"{GITHUB_API}{path}", params=params)
        except httpx.HTTPError:
            logger.warning("GitHub request failed for %s", path)
            raise ExternalServiceError(
                "Could not reach GitHub right now. Please try again shortly."
            ) from None
        if resp.status_code == 404:
            raise NotFoundError("We couldn't find that GitHub user or repository. Is it public?")
        if resp.status_code in (403, 429):
            if self._is_rate_limited(resp):
                raise RateLimitError(
                    "GitHub rate limit reached. Please try again in a few minutes."
                )
            logger.warning("GitHub returned 403 (not rate limiting) for %s", path)
            raise ExternalServiceError("GitHub refused access to that resource.")
        if resp.status_code >= 400:
            raise ExternalServiceError("GitHub returned an unexpected error. Please try again later.")
        return resp.json()

    @staticmethod
    def _is_rate_limited(resp: httpx.Response) -> bool:
        """Distinguish primary/secondary rate limiting from other 403s."""
        if resp.status_code == 429:
            return True
        if resp.headers.get("X-RateLimit-Remaining") == "0" or "Retry-After" in resp.headers:
            return True
        try:
            message = str(resp.json().get("message", "")).lower()
        except (ValueError, AttributeError):
            message = ""
        return "rate limit" in message

    async def _get_optional(
        self, client: httpx.AsyncClient, path: str, params: dict[str, Any] | None = None
    ) -> Any:
        """Like _get but returns None on 404/upstream errors (e.g. no commits/README)."""
        try:
            return await self._get(client, path, params)
        except (NotFoundError, ExternalServiceError):
            return None

    @staticmethod
    def _repo_summary(repo: dict[str, Any]) -> dict[str, Any]:
        return {
            "name": _clip(repo.get("name"), 100),
            "fork": bool(repo.get("fork")),
            "language": _clip(repo.get("language"), 50),
            "stars": int(repo.get("stargazers_count") or 0),
            "description": _clip(repo.get("description")),
        }

    @staticmethod
    async def _none() -> None:
        return None

    async def fetch_snapshot(self, target: GitHubTarget) -> dict[str, Any]:
        if self._client is not None:
            return await self._build(self._client, target)
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(10.0), headers=self._headers(), follow_redirects=False
        ) as client:
            return await self._build(client, target)

    async def _build(self, client: httpx.AsyncClient, target: GitHubTarget) -> dict[str, Any]:
        user = await self._get(client, f"/users/{target.username}")
        profile = {
            "login": _clip(user.get("login"), 50),
            "name": _clip(user.get("name"), 100),
            "bio": _clip(user.get("bio")),
            "type": user.get("type") if user.get("type") in ("User", "Organization") else "User",
            "followers": int(user.get("followers") or 0),
            "public_repos": int(user.get("public_repos") or 0),
        }
        snapshot: dict[str, Any] = {"target_type": target.target_type, "profile": profile}

        commits_path: str | None = None
        readme_path: str | None = None
        if target.repo:
            repo = await self._get(client, f"/repos/{target.username}/{target.repo}")
            snapshot["repo"] = self._repo_summary(repo)
            snapshot["top_repos"] = [snapshot["repo"]]
            commits_path = f"/repos/{target.username}/{target.repo}/commits"
            readme_path = f"/repos/{target.username}/{target.repo}/readme"
        else:
            repos = await self._get(
                client,
                f"/users/{target.username}/repos",
                {"sort": "pushed", "per_page": 100, "type": "owner"},
            )
            usable = [
                r
                for r in repos
                if isinstance(r, dict) and not r.get("fork") and not r.get("archived")
            ]
            ranked = sorted(
                usable, key=lambda r: int(r.get("stargazers_count") or 0), reverse=True
            )[:5]
            snapshot["top_repos"] = [self._repo_summary(r) for r in ranked]
            if ranked:
                name = str(ranked[0].get("name") or "")
                if REPO_RE.fullmatch(name):
                    commits_path = f"/repos/{target.username}/{name}/commits"
                    readme_path = f"/repos/{target.username}/{name}/readme"

        commits, readme = await asyncio.gather(
            self._get_optional(client, commits_path, {"per_page": 8})
            if commits_path
            else self._none(),
            self._get_optional(client, readme_path) if readme_path else self._none(),
        )
        messages: list[str] = []
        for c in commits or []:
            if isinstance(c, dict):
                msg = str((c.get("commit") or {}).get("message", "")).split("\n")[0]
                if msg:
                    messages.append(msg[:150])
        snapshot["recent_commits"] = messages[:8]

        readme_text = ""
        if isinstance(readme, dict) and readme.get("encoding") == "base64":
            try:
                readme_text = base64.b64decode(readme.get("content", "")).decode("utf-8", "replace")
            except ValueError:
                readme_text = ""
        snapshot["readme_snippet"] = readme_text[:README_MAX_CHARS]
        return snapshot
