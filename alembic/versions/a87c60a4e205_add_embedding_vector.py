"""add embedding vector

Revision ID: a87c60a4e205
Revises: 68dd3399129a
Create Date: 2026-01-05 18:57:07.280913

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "a87c60a4e205"
down_revision = "68dd3399129a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "fact_embeddings",
        sa.Column(
            "embedding",
            postgresql.ARRAY(sa.Float()),
            nullable=False,
            server_default=sa.text("'{}'::double precision[]"),
        ),
    )
    op.alter_column("fact_embeddings", "embedding", server_default=None)


def downgrade() -> None:
    op.drop_column("fact_embeddings", "embedding")
