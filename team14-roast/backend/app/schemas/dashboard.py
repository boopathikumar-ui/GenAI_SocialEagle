"""Dashboard and settings schemas."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class Totals(BaseModel):
    """All-time totals for the current user."""

    roasts: int
    public_roasts: int
    reactions_received: int


class DayCount(BaseModel):
    """Roasts created on a single day."""

    date: str
    count: int


class IntensitySplit(BaseModel):
    """Roast counts per intensity."""

    mild: int
    medium: int
    spicy: int


class LanguageCount(BaseModel):
    """Occurrences of a language among top repos."""

    language: str
    count: int


class TopRoast(BaseModel):
    """A roast ranked by reactions received."""

    id: int
    github_username: str
    intensity: Literal["mild", "medium", "spicy"]
    share_slug: str
    is_public: bool
    reaction_total: int
    created_at: datetime


class DashboardStats(BaseModel):
    """Response of GET /dashboard/stats."""

    totals: Totals
    roasts_per_day: list[DayCount]
    intensity_split: IntensitySplit
    top_languages: list[LanguageCount]
    top_roasts: list[TopRoast]


class VisibilityUpdate(BaseModel):
    """Body of PUT /settings/roasts-visibility."""

    is_public: bool


class VisibilityResult(BaseModel):
    """Number of roasts updated."""

    updated: int
