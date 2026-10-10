"""Reaction model (post-MVP feature, table created in Phase 1)."""
import enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.roast import Roast
    from app.models.user import User


class ReactionEmoji(str, enum.Enum):
    fire = "fire"
    skull = "skull"
    laugh = "laugh"
    clap = "clap"


def _values(enum_cls: type[enum.Enum]) -> list[str]:
    return [str(member.value) for member in enum_cls]


class Reaction(Base, TimestampMixin):
    __tablename__ = "reactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    roast_id: Mapped[int] = mapped_column(
        ForeignKey("roasts.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    emoji: Mapped[ReactionEmoji] = mapped_column(
        Enum(ReactionEmoji, name="reaction_emoji", values_callable=_values),
        nullable=False,
    )

    roast: Mapped["Roast"] = relationship(back_populates="reactions")
    user: Mapped["User"] = relationship(back_populates="reactions")

    __table_args__ = (
        UniqueConstraint("roast_id", "user_id", "emoji", name="uq_reaction_roast_user_emoji"),
    )
