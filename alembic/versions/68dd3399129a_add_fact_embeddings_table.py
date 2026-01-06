"""add fact embeddings table

Revision ID: 68dd3399129a
Revises: 0001_initial_schema
Create Date: 2026-01-05 18:40:29.671271

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "68dd3399129a"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "fact_embeddings",
        sa.Column(
            "fact_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("facts.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("vector_id", sa.Text(), nullable=False),
        sa.Column("embedding_model", sa.Text(), nullable=False),
        sa.Column("namespace", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        "fact_embeddings_namespace_idx",
        "fact_embeddings",
        ["namespace"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("fact_embeddings_namespace_idx", table_name="fact_embeddings")
    op.drop_table("fact_embeddings")
