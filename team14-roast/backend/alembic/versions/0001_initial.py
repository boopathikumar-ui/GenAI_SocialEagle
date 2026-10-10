"""initial schema: users, refresh_tokens, roasts, reactions

Revision ID: 0001
Revises:
Create Date: 2026-10-10
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _ts() -> list[sa.Column]:
    return [
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    ]


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=True),
        sa.Column("full_name", sa.String(100), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_verified", sa.Boolean(), nullable=False),
        sa.Column("is_admin", sa.Boolean(), nullable=False),
        sa.Column("oauth_provider", sa.String(50), nullable=True),
        *_ts(),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("token", sa.String(255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False),
        *_ts(),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("ix_refresh_tokens_token", "refresh_tokens", ["token"], unique=True)

    op.create_table(
        "roasts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("github_url", sa.String(500), nullable=False),
        sa.Column("github_username", sa.String(100), nullable=False),
        sa.Column(
            "target_type", sa.Enum("profile", "repo", name="target_type"), nullable=False
        ),
        sa.Column(
            "intensity", sa.Enum("mild", "medium", "spicy", name="intensity"), nullable=False
        ),
        sa.Column("roast_text", sa.Text(), nullable=False),
        sa.Column(
            "github_snapshot",
            sa.JSON().with_variant(postgresql.JSONB(), "postgresql"),
            nullable=True,
        ),
        sa.Column("is_public", sa.Boolean(), nullable=False),
        sa.Column("share_slug", sa.String(32), nullable=False),
        *_ts(),
    )
    op.create_index("ix_roasts_user_id", "roasts", ["user_id"])
    op.create_index("ix_roasts_share_slug", "roasts", ["share_slug"], unique=True)
    op.create_index("ix_roasts_is_public_created_at", "roasts", ["is_public", "created_at"])

    op.create_table(
        "reactions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "roast_id", sa.Integer(), sa.ForeignKey("roasts.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "emoji",
            sa.Enum("fire", "skull", "laugh", "clap", name="reaction_emoji"),
            nullable=False,
        ),
        *_ts(),
        sa.UniqueConstraint("roast_id", "user_id", "emoji", name="uq_reaction_roast_user_emoji"),
    )
    op.create_index("ix_reactions_roast_id", "reactions", ["roast_id"])
    op.create_index("ix_reactions_user_id", "reactions", ["user_id"])


def downgrade() -> None:
    op.drop_table("reactions")
    op.drop_table("roasts")
    op.drop_table("refresh_tokens")
    op.drop_table("users")
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        for name in ("reaction_emoji", "intensity", "target_type"):
            op.execute(f"DROP TYPE IF EXISTS {name}")
