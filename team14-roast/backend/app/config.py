"""Application settings loaded from environment variables."""
import json
from functools import lru_cache
from typing import Annotated, Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


ALGORITHM = "HS256"  # fixed on purpose: never env-configurable (algorithm-confusion hardening)
MIN_SECRET_KEY_LENGTH = 32
_PLACEHOLDER_SECRETS = frozenset(
    {
        "change-me",
        "changeme",
        "your-secret-key",
        "secret",
        "secret-key",
        "your_secret_key",
        "replace-me",
        "ci-test-secret-not-real",
    }
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # repo-root .env (shared with docker-compose) first; a backend/.env overrides it
        env_file=("../.env", ".env"),
        extra="ignore",
        hide_input_in_errors=True,
    )

    APP_NAME: str = "Team14-Roast"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: str
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    ANTHROPIC_API_KEY: str = ""
    ROAST_MODEL: str = "claude-haiku-4-5-20251001"
    GITHUB_TOKEN: str | None = None
    # Which backend writes the roasts. "fake" serves canned dev output and requires DEBUG=true.
    ROAST_PROVIDER: Literal["anthropic", "openai", "fake"] = "anthropic"
    OPENAI_API_KEY: str = ""
    OPENAI_ROAST_MODEL: str = "gpt-4o-mini"
    ROAST_DAILY_PER_IP_CAP: int = 30
    ROAST_DAILY_GLOBAL_CAP: int = 1000

    # NoDecode: pydantic-settings must not JSON-decode this itself, so a plain
    # comma-separated value works; split_origins below handles both forms.
    CORS_ORIGINS: Annotated[list[str], NoDecode] = ["http://localhost:5173"]
    FRONTEND_URL: str = "http://localhost:5173"
    # Optional explicit OAuth redirect URI (falls back to the request-derived one).
    GOOGLE_REDIRECT_URI: str = ""

    @model_validator(mode="after")
    def validate_fake_provider(self) -> "Settings":
        if self.ROAST_PROVIDER == "fake" and not self.DEBUG:
            raise ValueError("ROAST_PROVIDER=fake is dev-only and requires DEBUG=true")
        return self

    @model_validator(mode="after")
    def validate_secret_key(self) -> "Settings":
        if not self.DEBUG:
            key = self.SECRET_KEY.strip()
            if len(key) < MIN_SECRET_KEY_LENGTH or key.lower() in _PLACEHOLDER_SECRETS:
                raise ValueError(
                    "SECRET_KEY must be at least 32 characters and not a placeholder; generate "
                    'one with: python -c "import secrets;print(secrets.token_urlsafe(48))"'
                )
        return self

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            text = value.strip()
            if text.startswith("["):
                return json.loads(text)
            return [o.strip() for o in text.split(",") if o.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


settings = get_settings()
