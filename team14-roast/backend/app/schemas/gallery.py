"""Gallery and reaction schemas."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

EmojiName = Literal["fire", "skull", "laugh", "clap"]


class ReactionCounts(BaseModel):
    """Per-emoji reaction totals."""

    fire: int = 0
    skull: int = 0
    laugh: int = 0
    clap: int = 0


class GalleryRoast(BaseModel):
    """Public view of a roast; deliberately omits user_id, github_url and snapshot."""

    id: int
    github_username: str
    target_type: Literal["profile", "repo"]
    intensity: Literal["mild", "medium", "spicy"]
    roast_text: str
    share_slug: str
    created_at: datetime
    reaction_counts: ReactionCounts
    my_reactions: list[EmojiName] = Field(default_factory=list)


class GalleryPage(BaseModel):
    """Paginated gallery response."""

    items: list[GalleryRoast]
    total: int
    page: int
    page_size: int


class ReactionCreate(BaseModel):
    """Body for adding a reaction."""

    emoji: EmojiName


class ReactionState(BaseModel):
    """Current reaction state of one roast for the requesting user."""

    reaction_counts: ReactionCounts
    my_reactions: list[EmojiName]
