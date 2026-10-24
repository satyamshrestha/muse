from uuid import UUID

from sqlalchemy.orm import Session

from app.models.shared_note import SharedNote
from app.repositories.friend_group_repository import FriendGroupRepository
from app.repositories.group_membership_repository import (
    GroupMembershipRepository,
)
from app.repositories.shared_note_repository import SharedNoteRepository


class SharedNoteService:
    def __init__(self, db: Session):
        self.db = db
        self.note_repository = SharedNoteRepository(db)
        self.group_repository = FriendGroupRepository(db)
        self.membership_repository = GroupMembershipRepository(db)

    def _ensure_group_member(
        self,
        group_id: UUID,
        user_id: UUID,
    ) -> None:
        group = self.group_repository.get_by_id(group_id)

        if group is None:
            raise ValueError("Group not found")

        if not self.membership_repository.is_member(user_id, group_id):
            raise ValueError("User is not a member of this group")

    def create_note(
        self,
        group_id: UUID,
        user_id: UUID,
        title: str,
        content: str,
    ) -> SharedNote:
        self._ensure_group_member(group_id, user_id)

        note = self.note_repository.create(
            group_id=group_id,
            created_by=user_id,
            title=title,
            content=content,
        )
        self.db.commit()
        self.db.refresh(note)
        return note

    def get_note(
        self,
        group_id: UUID,
        note_id: UUID,
        user_id: UUID,
    ) -> SharedNote:
        self._ensure_group_member(group_id, user_id)

        note = self.note_repository.get_by_id_for_group(
            note_id=note_id,
            group_id=group_id,
        )

        if note is None:
            raise ValueError("Shared note not found")

        return note

    def list_notes(
        self,
        group_id: UUID,
        user_id: UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> list[SharedNote]:
        self._ensure_group_member(group_id, user_id)

        if limit < 1 or limit > 100:
            raise ValueError("Limit must be between 1 and 100")

        if offset < 0:
            raise ValueError("Offset cannot be negative")

        return self.note_repository.list_by_group(
            group_id=group_id,
            limit=limit,
            offset=offset,
        )

    def update_note(
        self,
        group_id: UUID,
        note_id: UUID,
        user_id: UUID,
        *,
        title: str,
        content: str,
    ) -> SharedNote:
        self._ensure_group_member(group_id, user_id)

        note = self.note_repository.get_by_id_for_group(
            note_id=note_id,
            group_id=group_id,
        )

        if note is None:
            raise ValueError("Shared note not found")

        if note.created_by != user_id:
            raise ValueError("Only the note creator can update it")

        updated_note = self.note_repository.update(
            note,
            title=title,
            content=content,
        )
        self.db.commit()
        self.db.refresh(updated_note)
        return updated_note

    def delete_note(
        self,
        group_id: UUID,
        note_id: UUID,
        user_id: UUID,
    ) -> bool:
        self._ensure_group_member(group_id, user_id)

        note = self.note_repository.get_by_id_for_group(
            note_id=note_id,
            group_id=group_id,
        )

        if note is None:
            raise ValueError("Shared note not found")

        if note.created_by != user_id:
            raise ValueError("Only the note creator can delete it")

        self.note_repository.delete(note)
        self.db.commit()
        return True