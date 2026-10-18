from uuid import uuid4

import pytest

from app.models.user import User
from app.services.mood_entry_service import (
    MoodEntryNotFoundError,
    MoodEntryService,
    MoodValidationError,
)


def create_user(db) -> User:
    user = User(
        email=f"{uuid4().hex}@example.com",
        password_hash="test-hash",
        display_name="Mood Service Test",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_create_normalizes_mood_and_note(db):
    user = create_user(db)
    service = MoodEntryService(db)

    entry = service.create(
        user.id,
        "  HAPPY ",
        4,
        "  Great day!  ",
    )

    assert entry.mood == "happy"
    assert entry.intensity == 4
    assert entry.note == "Great day!"


@pytest.mark.parametrize(
    "mood",
    ["", "unknown", "very happy"],
)
def test_create_rejects_unsupported_mood(db, mood):
    user = create_user(db)
    service = MoodEntryService(db)

    with pytest.raises(MoodValidationError):
        service.create(user.id, mood, 3)


@pytest.mark.parametrize("intensity", [0, 6, -1, True, 2.5])
def test_create_rejects_invalid_intensity(db, intensity):
    user = create_user(db)
    service = MoodEntryService(db)

    with pytest.raises(MoodValidationError):
        service.create(user.id, "happy", intensity)


def test_create_rejects_oversized_note(db):
    user = create_user(db)
    service = MoodEntryService(db)

    with pytest.raises(MoodValidationError):
        service.create(user.id, "happy", 3, "x" * 501)


def test_create_converts_blank_note_to_none(db):
    user = create_user(db)
    service = MoodEntryService(db)

    entry = service.create(user.id, "calm", 3, "   ")

    assert entry.note is None


def test_list_validates_pagination(db):
    user = create_user(db)
    service = MoodEntryService(db)

    with pytest.raises(MoodValidationError):
        service.list_for_user(user.id, limit=0)

    with pytest.raises(MoodValidationError):
        service.list_for_user(user.id, limit=101)

    with pytest.raises(MoodValidationError):
        service.list_for_user(user.id, offset=-1)


def test_entries_are_private_to_their_owner(db):
    owner = create_user(db)
    other_user = create_user(db)
    service = MoodEntryService(db)

    entry = service.create(owner.id, "calm", 3)

    with pytest.raises(MoodEntryNotFoundError):
        service.get_for_user(other_user.id, entry.id)

    with pytest.raises(MoodEntryNotFoundError):
        service.delete(other_user.id, entry.id)


def test_delete_mood_entry(db):
    user = create_user(db)
    service = MoodEntryService(db)

    entry = service.create(user.id, "tired", 2)
    service.delete(user.id, entry.id)

    with pytest.raises(MoodEntryNotFoundError):
        service.get_for_user(user.id, entry.id)