from uuid import uuid4

from app.models.mood_entry import MoodEntry
from app.models.user import User
from app.repositories.mood_entry_repository import MoodEntryRepository


def create_user(db) -> User:
    user = User(
        email=f"{uuid4().hex}@example.com",
        password_hash="test-hash",
        display_name="Mood Repository Test",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_create_mood_entry(db):
    user = create_user(db)
    repository = MoodEntryRepository(db)

    entry = repository.create(
        user_id=user.id,
        mood="happy",
        intensity=4,
        note="Had a productive day",
    )
    db.commit()
    db.refresh(entry)

    assert entry.id is not None
    assert entry.user_id == user.id
    assert entry.mood == "happy"
    assert entry.intensity == 4
    assert entry.note == "Had a productive day"
    assert entry.created_at is not None


def test_get_by_id_requires_matching_owner(db):
    owner = create_user(db)
    other_user = create_user(db)
    repository = MoodEntryRepository(db)

    entry = repository.create(
        owner.id, "calm", 3
    )
    db.commit()

    assert repository.get_by_id_for_user(
        entry.id, owner.id
    ) is not None

    assert repository.get_by_id_for_user(
        entry.id, other_user.id
    ) is None


def test_list_by_user_is_scoped_and_paginated(db):
    user = create_user(db)
    other_user = create_user(db)
    repository = MoodEntryRepository(db)

    first = repository.create(user.id, "happy", 4)
    db.commit()
    db.refresh(first)

    second = repository.create(user.id, "calm", 3)
    db.commit()
    db.refresh(second)

    repository.create(other_user.id, "sad", 2)
    db.commit()

    entries = repository.list_by_user(user.id)

    assert len(entries) == 2
    assert all(entry.user_id == user.id for entry in entries)

    # Entries are ordered newest first.
    assert entries[0].id == second.id
    assert entries[1].id == first.id

    page = repository.list_by_user(
        user.id, limit=1, offset=1
    )
    assert len(page) == 1
    assert page[0].id == first.id


def test_delete_mood_entry(db):
    user = create_user(db)
    repository = MoodEntryRepository(db)

    entry = repository.create(user.id, "tired", 2)
    db.commit()
    entry_id = entry.id

    repository.delete(entry)
    db.commit()

    assert repository.get_by_id_for_user(
        entry_id, user.id
    ) is None


def test_create_mood_entry_without_note(db):
    user = create_user(db)
    repository = MoodEntryRepository(db)

    entry = repository.create(
        user_id=user.id,
        mood="neutral",
        intensity=3,
    )
    db.commit()
    db.refresh(entry)

    assert entry.note is None