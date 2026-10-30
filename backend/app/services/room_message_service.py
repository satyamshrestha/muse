from uuid import UUID

from sqlalchemy.orm import Session

from app.models.room_message import RoomMessage
from app.repositories.group_membership_repository import (
    GroupMembershipRepository,
)
from app.repositories.room_message_repository import (
    RoomMessageRepository,
)


class RoomMessageService:
    def __init__(self, db: Session):
        self.db = db
        self.message_repository = RoomMessageRepository(db)
        self.membership_repository = GroupMembershipRepository(db)

    def _ensure_group_member(
        self,
        group_id: UUID,
        user_id: UUID,
    ) -> None:
        if not self.membership_repository.is_member(
            user_id,
            group_id,
        ):
            raise ValueError("User is not a member of this group")

    def _get_message(self, message_id: UUID) -> RoomMessage:
        message = self.message_repository.get_by_id(message_id)

        if message is None:
            raise ValueError("Room message not found")

        return message

    def create_message(
        self,
        group_id: UUID,
        user_id: UUID,
        content: str,
    ) -> RoomMessage:
        self._ensure_group_member(group_id, user_id)

        if not content.strip():
            raise ValueError("Message content must not be empty")

        message = self.message_repository.create(
            group_id=group_id,
            user_id=user_id,
            content=content,
        )
        self.db.commit()
        self.db.refresh(message)
        return message

    def get_group_messages(
        self,
        group_id: UUID,
        user_id: UUID,
    ) -> list[RoomMessage]:
        self._ensure_group_member(group_id, user_id)

        return self.message_repository.get_for_group(group_id)

    def delete_message(
        self,
        message_id: UUID,
        user_id: UUID,
    ) -> bool:
        message = self._get_message(message_id)

        self._ensure_group_member(message.group_id, user_id)

        if message.user_id != user_id:
            raise ValueError("Only the message creator can delete it")

        deleted = self.message_repository.delete(message_id)

        if deleted:
            self.db.commit()

        return deleted