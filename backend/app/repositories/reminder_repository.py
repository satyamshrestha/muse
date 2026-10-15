from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.reminder import Reminder


class ReminderRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        user_id: UUID,
        title: str,
        remind_at: datetime,
    ) -> Reminder:
        reminder = Reminder(
            user_id=user_id,
            title=title,
            remind_at=remind_at,
        )
        self.db.add(reminder)
        self.db.flush()
        return reminder

    def get_by_id_for_user(
        self,
        reminder_id: UUID,
        user_id: UUID,
    ) -> Reminder | None:
        statement = select(Reminder).where(
            Reminder.id == reminder_id,
            Reminder.user_id == user_id,
        )
        return self.db.scalar(statement)

    def list_by_user(
        self,
        user_id: UUID,
        limit: int = 20,
        offset: int = 0,
        completed: bool | None = None,
    ) -> list[Reminder]:
        statement = select(Reminder).where(
            Reminder.user_id == user_id
        )

        if completed is not None:
            statement = statement.where(
                Reminder.completed == completed
            )

        statement = (
            statement
            .order_by(Reminder.remind_at.asc(), Reminder.id.asc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.db.scalars(statement).all())

    def update(
        self,
        reminder: Reminder,
        *,
        title: str,
        remind_at: datetime,
    ) -> Reminder:
        reminder.title = title
        reminder.remind_at = remind_at
        self.db.flush()
        return reminder

    def set_completed(
        self,
        reminder: Reminder,
        completed: bool,
    ) -> Reminder:
        reminder.completed = completed
        self.db.flush()
        return reminder

    def delete(self, reminder: Reminder) -> None:
        self.db.delete(reminder)
        self.db.flush()