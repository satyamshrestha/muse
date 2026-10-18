from uuid import UUID

from sqlalchemy.orm import Session

from app.models.mood_entry import MoodEntry
from app.repositories.mood_entry_repository import MoodEntryRepository


class MoodValidationError(Exception):
    pass


class MoodEntryNotFoundError(Exception):
    pass


class MoodEntryService:
    ALLOWED_MOODS = {
        "happy",
        "sad",
        "angry",
        "anxious",
        "calm",
        "excited",
        "stressed",
        "tired",
        "neutral",
        "grateful",
        "lonely",
        "overwhelmed",
    }

    def __init__(self, db: Session):
        self.db = db
        self.repository = MoodEntryRepository(db)

    @classmethod
    def _validate_mood(cls, mood: str) -> str:
        if not isinstance(mood, str):
            raise MoodValidationError("Mood must be a string.")

        normalized = mood.strip().lower()

        if normalized not in cls.ALLOWED_MOODS:
            raise MoodValidationError(
                "Unsupported mood. Choose a supported mood."
            )

        return normalized

    @staticmethod
    def _validate_intensity(intensity: int) -> int:
        if isinstance(intensity, bool) or not isinstance(intensity, int):
            raise MoodValidationError(
                "Intensity must be an integer between 1 and 5."
            )

        if not 1 <= intensity <= 5:
            raise MoodValidationError(
                "Intensity must be between 1 and 5."
            )

        return intensity

    @staticmethod
    def _validate_note(note: str | None) -> str | None:
        if note is None:
            return None

        if not isinstance(note, str):
            raise MoodValidationError("Note must be a string.")

        normalized = note.strip()

        if len(normalized) > 500:
            raise MoodValidationError(
                "Note cannot exceed 500 characters."
            )

        return normalized or None

    def create(
        self,
        user_id: UUID,
        mood: str,
        intensity: int,
        note: str | None = None,
    ) -> MoodEntry:
        normalized_mood = self._validate_mood(mood)
        normalized_intensity = self._validate_intensity(intensity)
        normalized_note = self._validate_note(note)

        try:
            entry = self.repository.create(
                user_id=user_id,
                mood=normalized_mood,
                intensity=normalized_intensity,
                note=normalized_note,
            )
            self.db.commit()
            self.db.refresh(entry)
            return entry
        except Exception:
            self.db.rollback()
            raise

    def get_for_user(
        self,
        user_id: UUID,
        entry_id: UUID,
    ) -> MoodEntry:
        entry = self.repository.get_by_id_for_user(
            entry_id=entry_id,
            user_id=user_id,
        )

        if entry is None:
            raise MoodEntryNotFoundError("Mood entry not found.")

        return entry

    def list_for_user(
        self,
        user_id: UUID,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> list[MoodEntry]:
        if not 1 <= limit <= 100:
            raise MoodValidationError(
                "Limit must be between 1 and 100."
            )

        if offset < 0:
            raise MoodValidationError(
                "Offset cannot be negative."
            )

        return self.repository.list_by_user(
            user_id=user_id,
            limit=limit,
            offset=offset,
        )

    def delete(
        self,
        user_id: UUID,
        entry_id: UUID,
    ) -> None:
        entry = self.repository.get_by_id_for_user(
            entry_id=entry_id,
            user_id=user_id,
        )

        if entry is None:
            raise MoodEntryNotFoundError("Mood entry not found.")

        try:
            self.repository.delete(entry)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise