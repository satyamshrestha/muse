from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.models.user import User
from app.services.personal_note_service import (
    PersonalNoteNotFoundError,
    PersonalNoteService,
    PersonalNoteValidationError,
)


def create_user(db: Session) -> User:
    user = User(
        email=f"{uuid4().hex}@example.com",
        password_hash="test-hash",
        display_name="Personal Note Service Test User",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_create_normalizes_title_and_content(db: Session):
    user = create_user(db)
    service = PersonalNoteService(db)

    note = service.create(
        user.id,
        "  Study ideas  ",
        "  Review the project plan.  ",
    )

    assert note.title == "Study ideas"
    assert note.content == "Review the project plan."


@pytest.mark.parametrize("title", ["", "   ", "x" * 256, None])
def test_create_rejects_invalid_title(db: Session, title):
    user = create_user(db)
    service = PersonalNoteService(db)

    with pytest.raises(PersonalNoteValidationError):
        service.create(user.id, title, "Valid content")


@pytest.mark.parametrize("content", ["", "   ", None])
def test_create_rejects_empty_content(db: Session, content):
    user = create_user(db)
    service = PersonalNoteService(db)

    with pytest.raises(PersonalNoteValidationError):
        service.create(user.id, "Valid title", content)


def test_get_for_user_returns_owned_note(db: Session):
    user = create_user(db)
    service = PersonalNoteService(db)
    note = service.create(user.id, "My note", "My content")

    result = service.get_for_user(user.id, note.id)

    assert result.id == note.id


def test_get_for_user_rejects_another_users_note(db: Session):
    owner = create_user(db)
    another_user = create_user(db)
    service = PersonalNoteService(db)
    note = service.create(owner.id, "Private", "Private content")

    with pytest.raises(PersonalNoteNotFoundError):
        service.get_for_user(another_user.id, note.id)


@pytest.mark.parametrize("limit", [0, -1, 101, True, 2.5])
def test_list_for_user_rejects_invalid_limit(db: Session, limit):
    user = create_user(db)
    service = PersonalNoteService(db)

    with pytest.raises(PersonalNoteValidationError):
        service.list_for_user(user.id, limit=limit)


@pytest.mark.parametrize("offset", [-1, True, 1.5])
def test_list_for_user_rejects_invalid_offset(db: Session, offset):
    user = create_user(db)
    service = PersonalNoteService(db)

    with pytest.raises(PersonalNoteValidationError):
        service.list_for_user(user.id, offset=offset)


def test_update_normalizes_and_saves_note(db: Session):
    user = create_user(db)
    service = PersonalNoteService(db)
    note = service.create(user.id, "Old title", "Old content")

    updated = service.update(
        user.id,
        note.id,
        title="  New title ",
        content=" New content ",
    )

    assert updated.title == "New title"
    assert updated.content == "New content"


def test_update_rejects_another_users_note(db: Session):
    owner = create_user(db)
    another_user = create_user(db)
    service = PersonalNoteService(db)
    note = service.create(owner.id, "Private", "Private content")

    with pytest.raises(PersonalNoteNotFoundError):
        service.update(
            another_user.id,
            note.id,
            title="Changed",
            content="Changed content",
        )


def test_update_rejects_invalid_data(db: Session):
    user = create_user(db)
    service = PersonalNoteService(db)
    note = service.create(user.id, "Original", "Original content")

    with pytest.raises(PersonalNoteValidationError):
        service.update(
            user.id,
            note.id,
            title="   ",
            content="New content",
        )

    unchanged = service.get_for_user(user.id, note.id)
    assert unchanged.title == "Original"
    assert unchanged.content == "Original content"


def test_delete_removes_owned_note(db: Session):
    user = create_user(db)
    service = PersonalNoteService(db)
    note = service.create(user.id, "Temporary", "Delete me")

    service.delete(user.id, note.id)

    with pytest.raises(PersonalNoteNotFoundError):
        service.get_for_user(user.id, note.id)


def test_delete_rejects_another_users_note(db: Session):
    owner = create_user(db)
    another_user = create_user(db)
    service = PersonalNoteService(db)
    note = service.create(owner.id, "Private", "Private content")

    with pytest.raises(PersonalNoteNotFoundError):
        service.delete(another_user.id, note.id)

    assert service.get_for_user(owner.id, note.id).id == note.id