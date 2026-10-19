from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.personal_note import PersonalNote
from app.models.user import User
from app.repositories.personal_note_repository import (
    PersonalNoteRepository,
)


def create_user(db: Session) -> User:
    user = User(
        email=f"{uuid4().hex}@example.com",
        password_hash="test-hash",
        display_name="Personal Note Test User",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_create_personal_note(db: Session):
    user = create_user(db)
    repository = PersonalNoteRepository(db)

    note = repository.create(
        user_id=user.id,
        title="My first note",
        content="Remember this idea.",
    )
    db.commit()
    db.refresh(note)

    assert note.id is not None
    assert note.user_id == user.id
    assert note.title == "My first note"
    assert note.content == "Remember this idea."
    assert note.created_at is not None
    assert note.updated_at is not None


def test_get_by_id_for_user_returns_owned_note(db: Session):
    user = create_user(db)
    repository = PersonalNoteRepository(db)

    note = repository.create(user.id, "Private", "My content")
    db.commit()

    result = repository.get_by_id_for_user(note.id, user.id)

    assert result is not None
    assert result.id == note.id


def test_get_by_id_for_user_does_not_return_another_users_note(
    db: Session,
):
    owner = create_user(db)
    another_user = create_user(db)
    repository = PersonalNoteRepository(db)

    note = repository.create(owner.id, "Private", "Owner's content")
    db.commit()

    result = repository.get_by_id_for_user(note.id, another_user.id)

    assert result is None


def test_get_by_id_for_user_returns_none_for_unknown_id(db: Session):
    user = create_user(db)
    repository = PersonalNoteRepository(db)

    result = repository.get_by_id_for_user(uuid4(), user.id)

    assert result is None


def test_list_by_user_only_returns_owned_notes(db: Session):
    user = create_user(db)
    another_user = create_user(db)
    repository = PersonalNoteRepository(db)

    repository.create(user.id, "Mine", "My content")
    repository.create(another_user.id, "Theirs", "Their content")
    db.commit()

    notes = repository.list_by_user(user.id)

    assert len(notes) == 1
    assert notes[0].title == "Mine"
    assert all(note.user_id == user.id for note in notes)


def test_list_by_user_supports_pagination(db: Session):
    user = create_user(db)
    repository = PersonalNoteRepository(db)

    for number in range(3):
        repository.create(
            user.id,
            f"Note {number}",
            f"Content {number}",
        )
    db.commit()

    first_page = repository.list_by_user(user.id, limit=2, offset=0)
    second_page = repository.list_by_user(user.id, limit=2, offset=2)

    assert len(first_page) == 2
    assert len(second_page) == 1
    assert {note.id for note in first_page}.isdisjoint(
        {note.id for note in second_page}
    )


def test_update_personal_note(db: Session):
    user = create_user(db)
    repository = PersonalNoteRepository(db)

    note = repository.create(user.id, "Old title", "Old content")
    db.commit()

    updated = repository.update(
        note,
        title="New title",
        content="Updated content",
    )
    db.commit()
    db.refresh(updated)

    assert updated.title == "New title"
    assert updated.content == "Updated content"


def test_delete_personal_note(db: Session):
    user = create_user(db)
    repository = PersonalNoteRepository(db)

    note = repository.create(user.id, "Temporary", "Delete me")
    db.commit()
    note_id = note.id

    repository.delete(note)
    db.commit()

    assert repository.get_by_id_for_user(note_id, user.id) is None