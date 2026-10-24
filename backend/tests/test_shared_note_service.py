from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.models.friend_group import FriendGroup
from app.models.group_membership import GroupMembership
from app.models.shared_note import SharedNote
from app.models.user import User
from app.services.shared_note_service import SharedNoteService


def create_user(db: Session) -> User:
    user = User(
        email=f"{uuid4().hex}@example.com",
        password_hash="test-hash",
        display_name="Shared Note Service Tester",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_group(db: Session, user: User) -> FriendGroup:
    group = FriendGroup(name=f"Group-{uuid4().hex[:8]}")
    db.add(group)
    db.flush()

    db.add(
        GroupMembership(
            user_id=user.id,
            group_id=group.id,
        )
    )
    db.commit()
    db.refresh(group)
    return group


def add_member(db: Session, group: FriendGroup, user: User) -> None:
    db.add(
        GroupMembership(
            user_id=user.id,
            group_id=group.id,
        )
    )
    db.commit()


def test_create_shared_note(db: Session):
    user = create_user(db)
    group = create_group(db, user)
    service = SharedNoteService(db)

    note = service.create_note(
        group_id=group.id,
        user_id=user.id,
        title="Project plan",
        content="Discuss the next feature.",
    )

    assert note.id is not None
    assert note.group_id == group.id
    assert note.created_by == user.id
    assert note.title == "Project plan"
    assert note.content == "Discuss the next feature."


def test_create_shared_note_rejects_non_member(db: Session):
    owner = create_user(db)
    outsider = create_user(db)
    group = create_group(db, owner)
    service = SharedNoteService(db)

    with pytest.raises(ValueError, match="not a member"):
        service.create_note(
            group_id=group.id,
            user_id=outsider.id,
            title="Unauthorized",
            content="Should not be saved.",
        )


def test_create_shared_note_rejects_missing_group(db: Session):
    user = create_user(db)
    service = SharedNoteService(db)

    with pytest.raises(ValueError, match="Group not found"):
        service.create_note(
            group_id=uuid4(),
            user_id=user.id,
            title="Unknown group",
            content="Content",
        )


def test_get_shared_note(db: Session):
    user = create_user(db)
    group = create_group(db, user)
    service = SharedNoteService(db)

    created = service.create_note(
        group.id, user.id, "Meeting", "Meeting details."
    )

    result = service.get_note(group.id, created.id, user.id)

    assert result.id == created.id
    assert result.title == "Meeting"


def test_get_shared_note_rejects_non_member(db: Session):
    owner = create_user(db)
    outsider = create_user(db)
    group = create_group(db, owner)
    service = SharedNoteService(db)

    note = service.create_note(
        group.id, owner.id, "Meeting", "Meeting details."
    )

    with pytest.raises(ValueError, match="not a member"):
        service.get_note(group.id, note.id, outsider.id)


def test_get_shared_note_rejects_wrong_group(db: Session):
    user = create_user(db)
    group = create_group(db, user)
    other_group = create_group(db, user)
    service = SharedNoteService(db)

    note = service.create_note(
        group.id, user.id, "Meeting", "Meeting details."
    )

    with pytest.raises(ValueError, match="Shared note not found"):
        service.get_note(other_group.id, note.id, user.id)


def test_list_shared_notes(db: Session):
    user = create_user(db)
    group = create_group(db, user)
    service = SharedNoteService(db)

    first = service.create_note(group.id, user.id, "First", "One")
    second = service.create_note(group.id, user.id, "Second", "Two")

    notes = service.list_notes(group.id, user.id)

    assert len(notes) == 2
    assert {note.id for note in notes} == {first.id, second.id}


def test_list_shared_notes_rejects_non_member(db: Session):
    owner = create_user(db)
    outsider = create_user(db)
    group = create_group(db, owner)
    service = SharedNoteService(db)

    with pytest.raises(ValueError, match="not a member"):
        service.list_notes(group.id, outsider.id)


def test_list_shared_notes_validates_limit_and_offset(db: Session):
    user = create_user(db)
    group = create_group(db, user)
    service = SharedNoteService(db)

    with pytest.raises(ValueError, match="Limit must be between"):
        service.list_notes(group.id, user.id, limit=0)

    with pytest.raises(ValueError, match="Limit must be between"):
        service.list_notes(group.id, user.id, limit=101)

    with pytest.raises(ValueError, match="Offset cannot be negative"):
        service.list_notes(group.id, user.id, offset=-1)


def test_update_shared_note_by_creator(db: Session):
    user = create_user(db)
    group = create_group(db, user)
    service = SharedNoteService(db)

    note = service.create_note(
        group.id, user.id, "Old title", "Old content"
    )

    updated = service.update_note(
        group.id,
        note.id,
        user.id,
        title="New title",
        content="New content",
    )

    assert updated.title == "New title"
    assert updated.content == "New content"


def test_update_shared_note_rejects_non_creator(db: Session):
    owner = create_user(db)
    member = create_user(db)
    group = create_group(db, owner)
    add_member(db, group, member)
    service = SharedNoteService(db)

    note = service.create_note(
        group.id, owner.id, "Original", "Original content"
    )

    with pytest.raises(
        ValueError, match="Only the note creator can update it"
    ):
        service.update_note(
            group.id,
            note.id,
            member.id,
            title="Changed",
            content="Changed content",
        )


def test_update_shared_note_rejects_missing_note(db: Session):
    user = create_user(db)
    group = create_group(db, user)
    service = SharedNoteService(db)

    with pytest.raises(ValueError, match="Shared note not found"):
        service.update_note(
            group.id,
            uuid4(),
            user.id,
            title="Changed",
            content="Changed content",
        )


def test_delete_shared_note_by_creator(db: Session):
    user = create_user(db)
    group = create_group(db, user)
    service = SharedNoteService(db)

    note = service.create_note(
        group.id, user.id, "Temporary", "Delete this."
    )

    assert service.delete_note(group.id, note.id, user.id) is True

    with pytest.raises(ValueError, match="Shared note not found"):
        service.get_note(group.id, note.id, user.id)


def test_delete_shared_note_rejects_non_creator(db: Session):
    owner = create_user(db)
    member = create_user(db)
    group = create_group(db, owner)
    add_member(db, group, member)
    service = SharedNoteService(db)

    note = service.create_note(
        group.id, owner.id, "Keep this", "Original content."
    )

    with pytest.raises(
        ValueError, match="Only the note creator can delete it"
    ):
        service.delete_note(group.id, note.id, member.id)


def test_delete_shared_note_rejects_missing_note(db: Session):
    user = create_user(db)
    group = create_group(db, user)
    service = SharedNoteService(db)

    with pytest.raises(ValueError, match="Shared note not found"):
        service.delete_note(group.id, uuid4(), user.id)