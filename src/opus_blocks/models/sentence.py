import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from opus_blocks.db.base import Base


class Sentence(Base):
    __tablename__ = "sentences"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    paragraph_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("paragraphs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    order: Mapped[int] = mapped_column("order", Integer, nullable=False)
    sentence_type: Mapped[str] = mapped_column(String, nullable=False)
    text: Mapped[str] = mapped_column(String, nullable=False)
    is_user_edited: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    supported: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    verifier_failure_modes: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=False, default=list
    )
    verifier_explanation: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    __table_args__ = (
        CheckConstraint('"order" >= 1', name="sentences_order_check"),
        CheckConstraint(
            "sentence_type IN ('topic','evidence','conclusion','transition')",
            name="sentences_type_check",
        ),
        UniqueConstraint("paragraph_id", "order", name="sentences_paragraph_order_uq"),
    )
