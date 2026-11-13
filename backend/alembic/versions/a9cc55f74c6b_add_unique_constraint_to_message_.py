"""add unique constraint to message reactions

Revision ID: a9cc55f74c6b
Revises: 5bb706ca5391
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a9cc55f74c6b"
down_revision: Union[str, Sequence[str], None] = "5bb706ca5391"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_message_reaction_user",
        "message_reactions",
        ["message_id", "user_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_message_reaction_user",
        "message_reactions",
        type_="unique",
    )