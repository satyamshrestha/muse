from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.media import Media
from app.models.memory_media import MemoryMedia


class MediaRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        uploaded_by: UUID,
        object_key: str,
        media_type: str,
        mime_type: str,
    ) -> Media:
        media = Media(
            uploaded_by=uploaded_by,
            object_key=object_key,
            media_type=media_type,
            mime_type=mime_type,
        )
        self.db.add(media)
        self.db.flush()
        return media

    def get_by_id(
        self,
        media_id: UUID,
    ) -> Media | None:
        statement = select(Media).where(
            Media.id == media_id
        )
        return self.db.scalar(statement)

    def get_by_id_for_user(
        self,
        media_id: UUID,
        user_id: UUID,
    ) -> Media | None:
        statement = select(Media).where(
            Media.id == media_id,
            Media.uploaded_by == user_id,
        )
        return self.db.scalar(statement)

    def list_by_user(
        self,
        user_id: UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Media]:
        statement = (
            select(Media)
            .where(Media.uploaded_by == user_id)
            .order_by(
                Media.created_at.desc(),
                Media.id.desc(),
            )
            .offset(offset)
            .limit(limit)
        )
        return list(self.db.scalars(statement).all())

    def has_attachments(
        self,
        media_id: UUID,
    ) -> bool:
        statement = (
            select(MemoryMedia.id)
            .where(MemoryMedia.media_id == media_id)
            .limit(1)
        )
        return self.db.scalar(statement) is not None

    def delete(self, media: Media) -> None:
        self.db.delete(media)
        self.db.flush()