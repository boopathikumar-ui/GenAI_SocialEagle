"""Roast schemas."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class RoastCreate(BaseModel):
    github_url: str = Field(min_length=10, max_length=300)
    intensity: Literal["mild", "medium", "spicy"] = "medium"
    is_public: bool = False
    language: Literal["english", "thanglish"] = "english"


class RoastUpdate(BaseModel):
    is_public: bool


class RoastRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None
    github_url: str
    github_username: str
    target_type: Literal["profile", "repo"]
    intensity: Literal["mild", "medium", "spicy"]
    roast_text: str
    is_public: bool
    share_slug: str
    created_at: datetime


class RoastList(BaseModel):
    items: list[RoastRead]
    total: int
    page: int
    page_size: int
