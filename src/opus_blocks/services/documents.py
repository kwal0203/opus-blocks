import hashlib
from pathlib import Path
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from opus_blocks.core.config import settings
from opus_blocks.models.document import Document


def _compute_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def build_storage_path(owner_id: str, document_id: str, filename: str) -> Path:
    return Path(settings.storage_root) / owner_id / document_id / filename


async def get_document_by_hash(
    session: AsyncSession, owner_id: UUID, content_hash: str
) -> Document | None:
    result = await session.execute(
        select(Document).where(
            Document.owner_id == owner_id,
            Document.content_hash == content_hash,
        )
    )
    return result.scalar_one_or_none()


async def create_document(
    session: AsyncSession,
    owner_id: UUID,
    filename: str,
    content: bytes,
) -> Document:
    content_hash = _compute_hash(content)
    existing = await get_document_by_hash(session, owner_id, content_hash)
    if existing:
        return existing

    document = Document(
        owner_id=owner_id,
        source_type="PDF",
        filename=filename,
        content_hash=content_hash,
        storage_uri="",
        status="UPLOADED",
    )
    session.add(document)
    await session.flush()

    storage_path = build_storage_path(str(owner_id), str(document.id), filename)
    storage_path.parent.mkdir(parents=True, exist_ok=True)
    storage_path.write_bytes(content)
    document.storage_uri = str(storage_path)

    await session.commit()
    await session.refresh(document)
    return document


async def get_document(session: AsyncSession, owner_id: UUID, document_id: UUID) -> Document | None:
    result = await session.execute(
        select(Document).where(Document.id == document_id, Document.owner_id == owner_id)
    )
    return result.scalar_one_or_none()
