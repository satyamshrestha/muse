"""add timezone to notification preferences

Revision ID: 697729a341c6
Revises: a9cc55f74c6b
Create Date: 2026-11-14 17:56:41.328647
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "697729a341c6"
down_revision: Union[str, Sequence[str], None] = "a9cc55f74c6b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "notification_preferences",
        sa.Column(
            "timezone_name",
            sa.String(length=64),
            nullable=False,
            server_default="UTC",
        ),
    )


def downgrade() -> None:
    op.drop_column("notification_preferences", "timezone_name")