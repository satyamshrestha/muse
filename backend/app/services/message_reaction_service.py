from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.message_reaction import MessageReaction
from app.models.room_message import RoomMessage
from app.repositories.group_membership_repository import (
    GroupMembershipRepository,
)
from app.repositories.message_reaction_repository import (
    MessageReactionRepository,
)


class MessageReactionService:
    def __init__(self, db: Session):
        self.db = db
        self.reaction_repository = MessageReactionRepository(db)
        self.membership_repository = GroupMembershipRepository(db)

    def _get_message(self, message_id: UUID) -> RoomMessage:
        message = self.db.scalar(
            select(RoomMessage).where(RoomMessage.id == message_id)
        )

        if message is None:
            raise ValueError("Room message not found")

        return message

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

    def create_reaction(
        self,
        message_id: UUID,
        user_id: UUID,
        reaction: str,
    ) -> MessageReaction:
        message = self._get_message(message_id)
        self._ensure_group_member(message.group_id, user_id)

        if not reaction.strip():
            raise ValueError("Reaction must not be empty")

        existing = self.reaction_repository.get_for_user_and_message(
            user_id=user_id,
            message_id=message_id,
        )

        if existing is not None:
            raise ValueError("User has already reacted to this message")

        message_reaction = self.reaction_repository.create(
            message_id=message_id,
            user_id=user_id,
            reaction=reaction,
        )
        self.db.commit()
        self.db.refresh(message_reaction)
        return message_reaction

    def get_message_reactions(
        self,
        message_id: UUID,
        user_id: UUID,
    ) -> list[MessageReaction]:
        message = self._get_message(message_id)
        self._ensure_group_member(message.group_id, user_id)

        return self.reaction_repository.get_for_message(message_id)

    def update_reaction(
        self,
        reaction_id: UUID,
        user_id: UUID,
        reaction: str,
    ) -> MessageReaction:
        message_reaction = self.reaction_repository.get_by_id(reaction_id)

        if message_reaction is None:
            raise ValueError("Message reaction not found")

        if message_reaction.user_id != user_id:
            raise ValueError("Only the reaction creator can update it")

        message = self._get_message(message_reaction.message_id)
        self._ensure_group_member(message.group_id, user_id)

        if not reaction.strip():
            raise ValueError("Reaction must not be empty")

        updated = self.reaction_repository.update_reaction(
            message_reaction,
            reaction=reaction,
        )
        self.db.commit()
        self.db.refresh(updated)
        return updated

    def delete_reaction(
        self,
        reaction_id: UUID,
        user_id: UUID,
    ) -> bool:
        message_reaction = self.reaction_repository.get_by_id(reaction_id)

        if message_reaction is None:
            raise ValueError("Message reaction not found")

        if message_reaction.user_id != user_id:
            raise ValueError("Only the reaction creator can delete it")

        message = self._get_message(message_reaction.message_id)
        self._ensure_group_member(message.group_id, user_id)

        deleted = self.reaction_repository.delete(reaction_id)

        if deleted:
            self.db.commit()

        return deleted