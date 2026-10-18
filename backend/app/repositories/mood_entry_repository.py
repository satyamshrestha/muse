from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.mood_entry import MoodEntry


class MoodEntryRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        user_id: UUID,
        mood: str,
        intensity: int,
        note: str | None = None,
    ) -> MoodEntry:
        entry = MoodEntry(
            user_id=user_id,
            mood=mood,
            intensity=intensity,
            note=note,
        )
        self.db.add(entry)
        self.db.flush()
        return entry

    def get_by_id_for_user(
        self,
        entry_id: UUID,
        user_id: UUID,
    ) -> MoodEntry | None:
        statement = select(MoodEntry).where(
            MoodEntry.id == entry_id,
            MoodEntry.user_id == user_id,
        )
        return self.db.scalar(statement)

    def list_by_user(
        self,
        user_id: UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> list[MoodEntry]:
        statement = (
            select(MoodEntry)
            .where(MoodEntry.user_id == user_id)
            .order_by(
                MoodEntry.created_at.desc(),
                MoodEntry.id.desc(),
            )
            .offset(offset)
            .limit(limit)
        )
        return list(self.db.scalars(statement).all())

    def delete(self, entry: MoodEntry) -> None:
        self.db.delete(entry)
        self.db.flush()