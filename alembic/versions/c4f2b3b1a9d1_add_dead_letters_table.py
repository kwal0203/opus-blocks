"""Add dead_letters table.

Revision ID: c4f2b3b1a9d1
Revises: a87c60a4e205
Create Date: 2025-01-07 00:00:00.000000
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "c4f2b3b1a9d1"
down_revision = "a87c60a4e205"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "dead_letters",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("task_name", sa.String(), nullable=False),
        sa.Column("payload_json", postgresql.JSONB(), nullable=False),
        sa.Column("error", sa.String(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_dead_letters_job_id", "dead_letters", ["job_id"])
    op.create_foreign_key(
        "dead_letters_job_id_fkey",
        "dead_letters",
        "jobs",
        ["job_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("dead_letters_job_id_fkey", "dead_letters", type_="foreignkey")
    op.drop_index("ix_dead_letters_job_id", table_name="dead_letters")
    op.drop_table("dead_letters")
