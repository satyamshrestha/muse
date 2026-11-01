from datetime import date
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.daily_drop import DailyDrop
from app.repositories.daily_drop_repository import DailyDropRepository


class DailyDropService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = DailyDropRepository(db)

    def create_drop(
        self,
        user_id: UUID,
        title: str,
        content: str,
        drop_date: date,
        source: str,
    ) -> DailyDrop:
        if not title or not title.strip():
            raise ValueError("Title cannot be empty")

        if not content or not content.strip():
            raise ValueError("Content cannot be empty")

        if not source or not source.strip():
            raise ValueError("Source cannot be empty")

        if drop_date is None:
            raise ValueError("Drop date cannot be empty")

        drop = self.repository.create(
            user_id=user_id,
            title=title,
            content=content,
            drop_date=drop_date,
            source=source,
        )

        self.db.commit()
        self.db.refresh(drop)

        return drop

    def get_drop(self, user_id: UUID, drop_id: UUID) -> DailyDrop | None:
        drop = self.repository.get_by_id(drop_id)

        if drop is None or drop.user_id != user_id:
            return None

        return drop

    def get_user_drops(self, user_id: UUID) -> list[DailyDrop]:
        return self.repository.get_for_user(user_id)

    def get_drops_by_date(
        self,
        user_id: UUID,
        drop_date: date,
    ) -> list[DailyDrop]:
        return self.repository.get_by_date(user_id, drop_date)

    def delete_drop(self, user_id: UUID, drop_id: UUID) -> bool:
        drop = self.repository.get_by_id(drop_id)

        if drop is None or drop.user_id != user_id:
            raise ValueError("Daily drop not found")

        self.repository.delete(drop_id)
        self.db.commit()

        return True