from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.message_reaction import MessageReaction


class MessageReactionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        message_id: UUID,
        user_id: UUID,
        reaction: str,
    ) -> MessageReaction:
        message_reaction = MessageReaction(
            message_id=message_id,
            user_id=user_id,
            reaction=reaction,
        )
        self.db.add(message_reaction)
        self.db.flush()
        return message_reaction

    def get_by_id(
        self,
        reaction_id: UUID,
    ) -> MessageReaction | None:
        return self.db.scalar(
            select(MessageReaction).where(
                MessageReaction.id == reaction_id
            )
        )

    def get_for_message(
        self,
        message_id: UUID,
    ) -> list[MessageReaction]:
        statement = (
            select(MessageReaction)
            .where(MessageReaction.message_id == message_id)
            .order_by(MessageReaction.created_at.asc())
        )
        return list(self.db.scalars(statement))

    def get_for_user_and_message(
        self,
        user_id: UUID,
        message_id: UUID,
    ) -> MessageReaction | None:
        statement = select(MessageReaction).where(
            MessageReaction.user_id == user_id,
            MessageReaction.message_id == message_id,
        )
        return self.db.scalar(statement)

    def update_reaction(
        self,
        message_reaction: MessageReaction,
        *,
        reaction: str,
    ) -> MessageReaction:
        message_reaction.reaction = reaction
        self.db.flush()
        return message_reaction

    def delete(self, reaction_id: UUID) -> bool:
        result = self.db.execute(
            delete(MessageReaction).where(
                MessageReaction.id == reaction_id
            )
        )
        self.db.flush()
        return result.rowcount > 0