from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.friend_group import FriendGroup
from app.models.shared_note import SharedNote
from app.models.user import User
from app.repositories.shared_note_repository import SharedNoteRepository


def create_user(db: Session) -> User:
    user = User(
        email=f"{uuid4().hex}@example.com",
        password_hash="test-hash",
        display_name="Shared Note Test User",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_group(db: Session) -> FriendGroup:
    group = FriendGroup(name=f"Shared Notes {uuid4().hex[:8]}")
    db.add(group)
    db.commit()
    db.refresh(group)
    return group


def test_create_shared_note(db: Session):
    user = create_user(db)
    group = create_group(db)
    repository = SharedNoteRepository(db)

    note = repository.create(
        group_id=group.id,
        created_by=user.id,
        title="Project ideas",
        content="Discuss the next MUSE feature.",
    )
    db.commit()
    db.refresh(note)

    assert note.id is not None
    assert note.group_id == group.id
    assert note.created_by == user.id
    assert note.title == "Project ideas"
    assert note.content == "Discuss the next MUSE feature."
    assert note.created_at is not None
    assert note.updated_at is not None


def test_get_by_id_for_group_returns_matching_note(db: Session):
    user = create_user(db)
    group = create_group(db)
    repository = SharedNoteRepository(db)

    note = repository.create(
        group.id, user.id, "Meeting", "Meeting notes."
    )
    db.commit()

    result = repository.get_by_id_for_group(note.id, group.id)

    assert result is not None
    assert result.id == note.id


def test_get_by_id_for_group_hides_note_from_another_group(
    db: Session,
):
    user = create_user(db)
    group = create_group(db)
    another_group = create_group(db)
    repository = SharedNoteRepository(db)

    note = repository.create(
        group.id, user.id, "Meeting", "Private to this group."
    )
    db.commit()

    result = repository.get_by_id_for_group(
        note.id, another_group.id
    )

    assert result is None


def test_get_by_id_for_group_returns_none_for_unknown_id(
    db: Session,
):
    group = create_group(db)
    repository = SharedNoteRepository(db)

    result = repository.get_by_id_for_group(uuid4(), group.id)

    assert result is None


def test_list_by_group_only_returns_notes_for_that_group(
    db: Session,
):
    user = create_user(db)
    group = create_group(db)
    another_group = create_group(db)
    repository = SharedNoteRepository(db)

    repository.create(group.id, user.id, "First", "First note.")
    repository.create(group.id, user.id, "Second", "Second note.")
    repository.create(
        another_group.id, user.id, "Other", "Another group's note."
    )
    db.commit()

    notes = repository.list_by_group(group.id)

    assert len(notes) == 2
    assert {note.title for note in notes} == {"First", "Second"}
    assert all(note.group_id == group.id for note in notes)


def test_list_by_group_returns_empty_list_when_no_notes(
    db: Session,
):
    group = create_group(db)
    repository = SharedNoteRepository(db)

    assert repository.list_by_group(group.id) == []


def test_list_by_group_supports_pagination(db: Session):
    user = create_user(db)
    group = create_group(db)
    repository = SharedNoteRepository(db)

    for number in range(3):
        repository.create(
            group.id,
            user.id,
            f"Note {number}",
            f"Content {number}",
        )
    db.commit()

    first_page = repository.list_by_group(
        group.id, limit=2, offset=0
    )
    second_page = repository.list_by_group(
        group.id, limit=2, offset=2
    )

    assert len(first_page) == 2
    assert len(second_page) == 1
    assert {note.id for note in first_page}.isdisjoint(
        {note.id for note in second_page}
    )


def test_update_shared_note(db: Session):
    user = create_user(db)
    group = create_group(db)
    repository = SharedNoteRepository(db)

    note = repository.create(
        group.id, user.id, "Old title", "Old content"
    )
    db.commit()

    updated = repository.update(
        note,
        title="Updated title",
        content="Updated content",
    )
    db.commit()
    db.refresh(updated)

    assert updated.title == "Updated title"
    assert updated.content == "Updated content"


def test_delete_shared_note(db: Session):
    user = create_user(db)
    group = create_group(db)
    repository = SharedNoteRepository(db)

    note = repository.create(
        group.id, user.id, "Temporary", "Delete this note."
    )
    db.commit()
    note_id = note.id

    repository.delete(note)
    db.commit()

    assert repository.get_by_id_for_group(note_id, group.id) is None