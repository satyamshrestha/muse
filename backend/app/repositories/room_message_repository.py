from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.room_message import RoomMessage


class RoomMessageRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        group_id: UUID,
        user_id: UUID,
        content: str,
    ) -> RoomMessage:
        message = RoomMessage(
            group_id=group_id,
            user_id=user_id,
            content=content,
        )
        self.db.add(message)
        self.db.flush()
        return message

    def get_by_id(self, message_id: UUID) -> RoomMessage | None:
        return self.db.scalar(
            select(RoomMessage).where(RoomMessage.id == message_id)
        )

    def get_for_group(self, group_id: UUID) -> list[RoomMessage]:
        statement = (
            select(RoomMessage)
            .where(RoomMessage.group_id == group_id)
            .order_by(RoomMessage.created_at.asc())
        )
        return list(self.db.scalars(statement))

    def get_for_user(self, user_id: UUID) -> list[RoomMessage]:
        statement = (
            select(RoomMessage)
            .where(RoomMessage.user_id == user_id)
            .order_by(RoomMessage.created_at.asc())
        )
        return list(self.db.scalars(statement))

    def delete(self, message_id: UUID) -> bool:
        result = self.db.execute(
            delete(RoomMessage).where(RoomMessage.id == message_id)
        )
        self.db.flush()
        return result.rowcount > 0