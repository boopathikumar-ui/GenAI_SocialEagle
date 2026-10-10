"""Roast model."""
import enum
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Boolean, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.reaction import Reaction
    from app.models.user import User


class TargetType(str, enum.Enum):
    profile = "profile"
    repo = "repo"


class Intensity(str, enum.Enum):
    mild = "mild"
    medium = "medium"
    spicy = "spicy"


def _values(enum_cls: type[enum.Enum]) -> list[str]:
    return [str(member.value) for member in enum_cls]


class Roast(Base, TimestampMixin):
    __tablename__ = "roasts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True
    )
    github_url: Mapped[str] = mapped_column(String(500), nullable=False)
    github_username: Mapped[str] = mapped_column(String(100), nullable=False)
    target_type: Mapped[TargetType] = mapped_column(
        Enum(TargetType, name="target_type", values_callable=_values), nullable=False
    )
    intensity: Mapped[Intensity] = mapped_column(
        Enum(Intensity, name="intensity", values_callable=_values),
        default=Intensity.medium,
        nullable=False,
    )
    roast_text: Mapped[str] = mapped_column(Text, nullable=False)
    github_snapshot: Mapped[dict[str, Any] | None] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=True
    )
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    share_slug: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)

    user: Mapped["User | None"] = relationship(back_populates="roasts")
    reactions: Mapped[list["Reaction"]] = relationship(
        back_populates="roast", cascade="all, delete-orphan", passive_deletes=True
    )

    __table_args__ = (
        Index("ix_roasts_is_public_created_at", "is_public", "created_at"),
        Index("ix_roasts_user_id_created_at", "user_id", "created_at"),
    )
