from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.personal_note import PersonalNote


class PersonalNoteRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        user_id: UUID,
        title: str,
        content: str,
    ) -> PersonalNote:
        note = PersonalNote(
            user_id=user_id,
            title=title,
            content=content,
        )
        self.db.add(note)
        self.db.flush()
        return note

    def get_by_id_for_user(
        self,
        note_id: UUID,
        user_id: UUID,
    ) -> PersonalNote | None:
        statement = select(PersonalNote).where(
            PersonalNote.id == note_id,
            PersonalNote.user_id == user_id,
        )
        return self.db.scalar(statement)

    def list_by_user(
        self,
        user_id: UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> list[PersonalNote]:
        statement = (
            select(PersonalNote)
            .where(PersonalNote.user_id == user_id)
            .order_by(
                PersonalNote.created_at.desc(),
                PersonalNote.id.desc(),
            )
            .offset(offset)
            .limit(limit)
        )
        return list(self.db.scalars(statement).all())

    def update(
        self,
        note: PersonalNote,
        *,
        title: str,
        content: str,
    ) -> PersonalNote:
        note.title = title
        note.content = content
        self.db.flush()
        return note

    def delete(self, note: PersonalNote) -> None:
        self.db.delete(note)
        self.db.flush()