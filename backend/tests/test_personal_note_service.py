from uuid import UUID

from sqlalchemy.orm import Session

from app.models.personal_note import PersonalNote
from app.repositories.personal_note_repository import PersonalNoteRepository


class PersonalNoteValidationError(Exception):
    pass


class PersonalNoteNotFoundError(Exception):
    pass


class PersonalNoteService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = PersonalNoteRepository(db)

    @staticmethod
    def _validate_title(title: str) -> str:
        if not isinstance(title, str):
            raise PersonalNoteValidationError("Title must be a string.")

        title = title.strip()

        if not title:
            raise PersonalNoteValidationError("Title cannot be empty.")

        if len(title) > 255:
            raise PersonalNoteValidationError(
                "Title cannot exceed 255 characters."
            )

        return title

    @staticmethod
    def _validate_content(content: str) -> str:
        if not isinstance(content, str):
            raise PersonalNoteValidationError("Content must be a string.")

        content = content.strip()

        if not content:
            raise PersonalNoteValidationError("Content cannot be empty.")

        return content

    def create(
        self,
        user_id: UUID,
        title: str,
        content: str,
    ) -> PersonalNote:
        normalized_title = self._validate_title(title)
        normalized_content = self._validate_content(content)

        try:
            note = self.repository.create(
                user_id=user_id,
                title=normalized_title,
                content=normalized_content,
            )
            self.db.commit()
            self.db.refresh(note)
            return note
        except Exception:
            self.db.rollback()
            raise

    def get_for_user(
        self,
        user_id: UUID,
        note_id: UUID,
    ) -> PersonalNote:
        note = self.repository.get_by_id_for_user(
            note_id=note_id,
            user_id=user_id,
        )

        if note is None:
            raise PersonalNoteNotFoundError("Personal note not found.")

        return note

    def list_for_user(
        self,
        user_id: UUID,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> list[PersonalNote]:
        if isinstance(limit, bool) or not isinstance(limit, int):
            raise PersonalNoteValidationError(
                "Limit must be an integer between 1 and 100."
            )

        if not 1 <= limit <= 100:
            raise PersonalNoteValidationError(
                "Limit must be between 1 and 100."
            )

        if isinstance(offset, bool) or not isinstance(offset, int):
            raise PersonalNoteValidationError(
                "Offset must be a non-negative integer."
            )

        if offset < 0:
            raise PersonalNoteValidationError(
                "Offset cannot be negative."
            )

        return self.repository.list_by_user(
            user_id=user_id,
            limit=limit,
            offset=offset,
        )

    def update(
        self,
        user_id: UUID,
        note_id: UUID,
        *,
        title: str,
        content: str,
    ) -> PersonalNote:
        note = self.repository.get_by_id_for_user(
            note_id=note_id,
            user_id=user_id,
        )

        if note is None:
            raise PersonalNoteNotFoundError("Personal note not found.")

        normalized_title = self._validate_title(title)
        normalized_content = self._validate_content(content)

        try:
            updated_note = self.repository.update(
                note,
                title=normalized_title,
                content=normalized_content,
            )
            self.db.commit()
            self.db.refresh(updated_note)
            return updated_note
        except Exception:
            self.db.rollback()
            raise

    def delete(self, user_id: UUID, note_id: UUID) -> None:
        note = self.repository.get_by_id_for_user(
            note_id=note_id,
            user_id=user_id,
        )

        if note is None:
            raise PersonalNoteNotFoundError("Personal note not found.")

        try:
            self.repository.delete(note)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise