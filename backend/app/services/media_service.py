from uuid import UUID

from sqlalchemy.orm import Session

from app.models.media import Media
from app.repositories.media_repository import MediaRepository


class MediaService:
    def __init__(self, db: Session):
        self.db = db
        self.media_repository = MediaRepository(db)

    def register_media(
        self,
        user_id: UUID,
        object_key: str,
        media_type: str,
        mime_type: str,
    ) -> Media:
        object_key = object_key.strip()
        media_type = media_type.strip()
        mime_type = mime_type.strip()

        if not object_key:
            raise ValueError("Object key cannot be empty")

        if len(object_key) > 500:
            raise ValueError("Object key cannot exceed 500 characters")

        if not media_type:
            raise ValueError("Media type cannot be empty")

        if len(media_type) > 50:
            raise ValueError("Media type cannot exceed 50 characters")

        if not mime_type:
            raise ValueError("MIME type cannot be empty")

        if len(mime_type) > 100:
            raise ValueError("MIME type cannot exceed 100 characters")

        media = self.media_repository.create(
            uploaded_by=user_id,
            object_key=object_key,
            media_type=media_type,
            mime_type=mime_type,
        )

        self.db.commit()
        self.db.refresh(media)
        return media

    def get_media(
        self,
        media_id: UUID,
        user_id: UUID,
    ) -> Media:
        media = self.media_repository.get_by_id_for_user(
            media_id=media_id,
            user_id=user_id,
        )

        if media is None:
            raise ValueError("Media not found")

        return media

    def list_media(
        self,
        user_id: UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Media]:
        if limit < 1 or limit > 100:
            raise ValueError("Limit must be between 1 and 100")

        if offset < 0:
            raise ValueError("Offset cannot be negative")

        return self.media_repository.list_by_user(
            user_id=user_id,
            limit=limit,
            offset=offset,
        )

    def delete_media(
        self,
        media_id: UUID,
        user_id: UUID,
    ) -> bool:
        media = self.media_repository.get_by_id_for_user(
            media_id=media_id,
            user_id=user_id,
        )

        if media is None:
            raise ValueError("Media not found")

        if self.media_repository.has_attachments(media_id):
            raise ValueError(
                "Cannot delete media while it is attached to memories"
            )

        self.media_repository.delete(media)
        self.db.commit()
        return True