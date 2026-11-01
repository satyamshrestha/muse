from datetime import date
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.daily_drop import DailyDrop


class DailyDropRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        user_id: UUID,
        title: str,
        content: str,
        drop_date: date,
        source: str,
    ) -> DailyDrop:
        drop = DailyDrop(
            user_id=user_id,
            title=title,
            content=content,
            drop_date=drop_date,
            source=source,
        )
        self.db.add(drop)
        self.db.flush()
        return drop

    def get_by_id(self, drop_id: UUID) -> DailyDrop | None:
        return self.db.scalar(
            select(DailyDrop).where(DailyDrop.id == drop_id)
        )

    def get_for_user(self, user_id: UUID) -> list[DailyDrop]:
        statement = (
            select(DailyDrop)
            .where(DailyDrop.user_id == user_id)
            .order_by(DailyDrop.drop_date.desc())
        )
        return list(self.db.scalars(statement))

    def get_by_date(
        self,
        user_id: UUID,
        drop_date: date,
    ) -> list[DailyDrop]:
        statement = (
            select(DailyDrop)
            .where(
                DailyDrop.user_id == user_id,
                DailyDrop.drop_date == drop_date,
            )
            .order_by(DailyDrop.created_at.asc())
        )
        return list(self.db.scalars(statement))

    def delete(self, drop_id: UUID) -> bool:
        result = self.db.execute(
            delete(DailyDrop).where(DailyDrop.id == drop_id)
        )
        self.db.flush()
        return result.rowcount > 0