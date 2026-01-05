import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from opus_blocks.db.base import Base


class Fact(Base):
    __tablename__ = "facts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=True, index=True
    )
    span_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("spans.id", ondelete="SET NULL"), nullable=True
    )

    source_type: Mapped[str] = mapped_column(String, nullable=False, index=True)
    content: Mapped[str] = mapped_column(String, nullable=False)
    qualifiers: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    is_uncertain: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_by: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        CheckConstraint("source_type IN ('PDF','MANUAL')", name="facts_source_type_check"),
        CheckConstraint("confidence >= 0 AND confidence <= 1", name="facts_confidence_check"),
        CheckConstraint(
            "created_by IN ('LIBRARIAN','USER')",
            name="facts_created_by_check",
        ),
        CheckConstraint(
            "(source_type = 'PDF' AND document_id IS NOT NULL) OR (source_type = 'MANUAL')",
            name="facts_pdf_document_check",
        ),
    )
