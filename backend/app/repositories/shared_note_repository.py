from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.shared_note import SharedNote


class SharedNoteRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        group_id: UUID,
        created_by: UUID,
        title: str,
        content: str,
    ) -> SharedNote:
        note = SharedNote(
            group_id=group_id,
            created_by=created_by,
            title=title,
            content=content,
        )
        self.db.add(note)
        self.db.flush()
        return note

    def get_by_id_for_group(
        self,
        note_id: UUID,
        group_id: UUID,
    ) -> SharedNote | None:
        statement = select(SharedNote).where(
            SharedNote.id == note_id,
            SharedNote.group_id == group_id,
        )
        return self.db.scalar(statement)

    def list_by_group(
        self,
        group_id: UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> list[SharedNote]:
        statement = (
            select(SharedNote)
            .where(SharedNote.group_id == group_id)
            .order_by(
                SharedNote.created_at.desc(),
                SharedNote.id.desc(),
            )
            .offset(offset)
            .limit(limit)
        )
        return list(self.db.scalars(statement).all())

    def update(
        self,
        note: SharedNote,
        *,
        title: str,
        content: str,
    ) -> SharedNote:
        note.title = title
        note.content = content
        self.db.flush()
        return note

    def delete(self, note: SharedNote) -> None:
        self.db.delete(note)
        self.db.flush()