from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.reminder import Reminder
from app.repositories.reminder_repository import ReminderRepository


class ReminderNotFoundError(Exception):
    pass


class ReminderValidationError(Exception):
    pass


class ReminderService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = ReminderRepository(db)

    @staticmethod
    def _validate_title(title: str) -> str:
        title = title.strip()

        if not title:
            raise ReminderValidationError(
                "Reminder title cannot be empty."
            )

        if len(title) > 255:
            raise ReminderValidationError(
                "Reminder title cannot exceed 255 characters."
            )

        return title

    @staticmethod
    def _validate_remind_at(remind_at: datetime) -> datetime:
        if remind_at.tzinfo is None or remind_at.utcoffset() is None:
            raise ReminderValidationError(
                "Reminder time must include a timezone."
            )

        if remind_at <= datetime.now(timezone.utc):
            raise ReminderValidationError(
                "Reminder time must be in the future."
            )

        return remind_at

    def create(
        self,
        user_id: UUID,
        title: str,
        remind_at: datetime,
    ) -> Reminder:
        title = self._validate_title(title)
        remind_at = self._validate_remind_at(remind_at)

        try:
            reminder = self.repository.create(
                user_id=user_id,
                title=title,
                remind_at=remind_at,
            )
            self.db.commit()
            self.db.refresh(reminder)
            return reminder
        except Exception:
            self.db.rollback()
            raise

    def list_for_user(
        self,
        user_id: UUID,
        *,
        limit: int = 20,
        offset: int = 0,
        completed: bool | None = None,
    ) -> list[Reminder]:
        if not 1 <= limit <= 100:
            raise ReminderValidationError(
                "Limit must be between 1 and 100."
            )

        if offset < 0:
            raise ReminderValidationError(
                "Offset cannot be negative."
            )

        return self.repository.list_by_user(
            user_id=user_id,
            limit=limit,
            offset=offset,
            completed=completed,
        )

    def update(
        self,
        user_id: UUID,
        reminder_id: UUID,
        *,
        title: str,
        remind_at: datetime,
    ) -> Reminder:
        title = self._validate_title(title)
        remind_at = self._validate_remind_at(remind_at)

        reminder = self.repository.get_by_id_for_user(
            reminder_id=reminder_id,
            user_id=user_id,
        )
        if reminder is None:
            raise ReminderNotFoundError(
                "Reminder not found."
            )

        try:
            self.repository.update(
                reminder,
                title=title,
                remind_at=remind_at,
            )
            self.db.commit()
            self.db.refresh(reminder)
            return reminder
        except Exception:
            self.db.rollback()
            raise

    def set_completed(
        self,
        user_id: UUID,
        reminder_id: UUID,
        completed: bool = True,
    ) -> Reminder:
        reminder = self.repository.get_by_id_for_user(
            reminder_id=reminder_id,
            user_id=user_id,
        )
        if reminder is None:
            raise ReminderNotFoundError(
                "Reminder not found."
            )

        try:
            self.repository.set_completed(reminder, completed)
            self.db.commit()
            self.db.refresh(reminder)
            return reminder
        except Exception:
            self.db.rollback()
            raise

    def delete(
        self,
        user_id: UUID,
        reminder_id: UUID,
    ) -> None:
        reminder = self.repository.get_by_id_for_user(
            reminder_id=reminder_id,
            user_id=user_id,
        )
        if reminder is None:
            raise ReminderNotFoundError(
                "Reminder not found."
            )

        try:
            self.repository.delete(reminder)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise