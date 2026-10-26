from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.memory_media import MemoryMedia


class MemoryMediaRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        memory_id: UUID,
        media_id: UUID,
    ) -> MemoryMedia:
        link = MemoryMedia(
            memory_id=memory_id,
            media_id=media_id,
        )
        self.db.add(link)
        self.db.flush()
        return link

    def get_by_id(
        self,
        link_id: UUID,
    ) -> MemoryMedia | None:
        statement = select(MemoryMedia).where(
            MemoryMedia.id == link_id
        )
        return self.db.scalar(statement)

    def get_by_memory_and_media(
        self,
        memory_id: UUID,
        media_id: UUID,
    ) -> MemoryMedia | None:
        statement = select(MemoryMedia).where(
            MemoryMedia.memory_id == memory_id,
            MemoryMedia.media_id == media_id,
        )
        return self.db.scalar(statement)

    def list_by_memory(
        self,
        memory_id: UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> list[MemoryMedia]:
        statement = (
            select(MemoryMedia)
            .where(MemoryMedia.memory_id == memory_id)
            .order_by(
                MemoryMedia.created_at.desc(),
                MemoryMedia.id.desc(),
            )
            .offset(offset)
            .limit(limit)
        )
        return list(self.db.scalars(statement).all())

    def delete(self, link: MemoryMedia) -> None:
        self.db.delete(link)
        self.db.flush()