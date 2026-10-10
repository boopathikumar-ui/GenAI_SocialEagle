"""add roasts(user_id, created_at) and refresh_tokens(expires_at) indexes

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-10
"""
from collections.abc import Sequence

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index("ix_roasts_user_id_created_at", "roasts", ["user_id", "created_at"])
    op.create_index("ix_refresh_tokens_expires_at", "refresh_tokens", ["expires_at"])


def downgrade() -> None:
    op.drop_index("ix_refresh_tokens_expires_at", table_name="refresh_tokens")
    op.drop_index("ix_roasts_user_id_created_at", table_name="roasts")
