from uuid import UUID

from sqlalchemy.orm import Session

from app.models.memory import Memory
from app.repositories.friend_group_repository import FriendGroupRepository
from app.repositories.group_membership_repository import (
    GroupMembershipRepository,
)
from app.repositories.memory_repository import MemoryRepository


class MemoryService:
    def __init__(self, db: Session):
        self.db = db
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

    def create_memory(
        self,
        group_id: UUID,
        user_id: UUID,
        title: str,
        description: str | None = None,
        memory_date=None,
    ) -> Memory:
        self._ensure_group_member(group_id, user_id)

        memory = self.memory_repository.create(
            group_id=group_id,
            created_by=user_id,
            title=title,
            description=description,
            memory_date=memory_date,
        )
        self.db.commit()
        self.db.refresh(memory)
        return memory

    def get_memory(
        self,
        group_id: UUID,
        memory_id: UUID,
        user_id: UUID,
    ) -> Memory:
        self._ensure_group_member(group_id, user_id)

        memory = self.memory_repository.get_by_id_for_group(
            memory_id=memory_id,
            group_id=group_id,
        )

        if memory is None:
            raise ValueError("Memory not found")

        return memory

    def list_memories(
        self,
        group_id: UUID,
        user_id: UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Memory]:
        self._ensure_group_member(group_id, user_id)

        if limit < 1 or limit > 100:
            raise ValueError("Limit must be between 1 and 100")

        if offset < 0:
            raise ValueError("Offset cannot be negative")

        return self.memory_repository.list_by_group(
            group_id=group_id,
            limit=limit,
            offset=offset,
        )

    def update_memory(
        self,
        group_id: UUID,
        memory_id: UUID,
        user_id: UUID,
        *,
        title: str,
        description: str | None,
        memory_date=None,
    ) -> Memory:
        self._ensure_group_member(group_id, user_id)

        memory = self.memory_repository.get_by_id_for_group(
            memory_id=memory_id,
            group_id=group_id,
        )

        if memory is None:
            raise ValueError("Memory not found")

        if memory.created_by != user_id:
            raise ValueError("Only the memory creator can update it")

        updated_memory = self.memory_repository.update(
            memory,
            title=title,
            description=description,
            memory_date=memory_date,
        )
        self.db.commit()
        self.db.refresh(updated_memory)
        return updated_memory

    def delete_memory(
        self,
        group_id: UUID,
        memory_id: UUID,
        user_id: UUID,
    ) -> bool:
        self._ensure_group_member(group_id, user_id)

        memory = self.memory_repository.get_by_id_for_group(
            memory_id=memory_id,
            group_id=group_id,
        )

        if memory is None:
            raise ValueError("Memory not found")

        if memory.created_by != user_id:
            raise ValueError("Only the memory creator can delete it")

        self.memory_repository.delete(memory)
        self.db.commit()
        return True