from uuid import UUID

from sqlalchemy.orm import Session

from app.models.media import Media
from app.models.memory_media import MemoryMedia
from app.repositories.friend_group_repository import FriendGroupRepository
from app.repositories.group_membership_repository import (
    GroupMembershipRepository,
)
from app.repositories.memory_media_repository import MemoryMediaRepository
from app.repositories.memory_repository import MemoryRepository


class MemoryMediaService:
    def __init__(self, db: Session):
        self.db = db
        self.memory_media_repository = MemoryMediaRepository(db)
        self.memory_repository = MemoryRepository(db)
        self.group_repository = FriendGroupRepository(db)
        self.membership_repository = GroupMembershipRepository(db)

    def _ensure_group_member(
        self,
        group_id: UUID,
        user_id: UUID,
    ) -> None:
        group = self.group_repository.get_by_id(group_id)

        if group is None:
            raise ValueError("Group not found")

        if not self.membership_repository.is_member(user_id, group_id):
            raise ValueError("User is not a member of this group")

    def _get_memory(
        self,
        group_id: UUID,
        memory_id: UUID,
    ):
        memory = self.memory_repository.get_by_id_for_group(
            memory_id=memory_id,
            group_id=group_id,
        )

        if memory is None:
            raise ValueError("Memory not found")

        return memory

    def attach_media(
        self,
        group_id: UUID,
        memory_id: UUID,
        media_id: UUID,
        user_id: UUID,
    ) -> MemoryMedia:
        self._ensure_group_member(group_id, user_id)
        self._get_memory(group_id, memory_id)

        media = self.db.get(Media, media_id)

        if media is None:
            raise ValueError("Media not found")

        if media.uploaded_by != user_id:
            raise ValueError("Only the media uploader can attach this media")

        existing_link = (
            self.memory_media_repository.get_by_memory_and_media(
                memory_id=memory_id,
                media_id=media_id,
            )
        )

        if existing_link is not None:
            raise ValueError("Media is already attached to this memory")

        link = self.memory_media_repository.create(
            memory_id=memory_id,
            media_id=media_id,
        )
        self.db.commit()
        self.db.refresh(link)
        return link

    def list_memory_media(
        self,
        group_id: UUID,
        memory_id: UUID,
        user_id: UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> list[MemoryMedia]:
        self._ensure_group_member(group_id, user_id)
        self._get_memory(group_id, memory_id)

        if limit < 1 or limit > 100:
            raise ValueError("Limit must be between 1 and 100")

        if offset < 0:
            raise ValueError("Offset cannot be negative")

        return self.memory_media_repository.list_by_memory(
            memory_id=memory_id,
            limit=limit,
            offset=offset,
        )

    def detach_media(
        self,
        group_id: UUID,
        memory_id: UUID,
        link_id: UUID,
        user_id: UUID,
    ) -> bool:
        self._ensure_group_member(group_id, user_id)
        memory = self._get_memory(group_id, memory_id)

        if memory.created_by != user_id:
            raise ValueError("Only the memory creator can detach media")

        link = self.memory_media_repository.get_by_id(link_id)

        if link is None or link.memory_id != memory_id:
            raise ValueError("Memory media link not found")

        self.memory_media_repository.delete(link)
        self.db.commit()
        return True