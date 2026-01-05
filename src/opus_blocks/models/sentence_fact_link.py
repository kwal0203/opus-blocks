import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from opus_blocks.db.base import Base


class SentenceFactLink(Base):
    __tablename__ = "sentence_fact_links"

    sentence_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sentences.id", ondelete="CASCADE"),
        primary_key=True,
    )
    fact_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("facts.id", ondelete="CASCADE"),
        primary_key=True,
    )
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "score IS NULL OR (score >= 0 AND score <= 1)",
            name="sentence_fact_links_score_check",
        ),
    )
