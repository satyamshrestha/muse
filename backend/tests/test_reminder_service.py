from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.models.user import User
from app.services.reminder_service import (
    ReminderNotFoundError,
    ReminderService,
    ReminderValidationError,
)


def create_user(db) -> User:
    user = User(
        email=f"{uuid4().hex}@example.com",
        password_hash="test-hash",
        display_name="Reminder Service Test",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def future_time(**kwargs) -> datetime:
    return datetime.now(timezone.utc) + timedelta(**kwargs)


def test_create_reminder_strips_title_and_persists(db):
    user = create_user(db)
    service = ReminderService(db)

    reminder = service.create(
        user.id,
        "  Study Korean  ",
        future_time(hours=1),
    )

    assert reminder.title == "Study Korean"
    assert reminder.user_id == user.id
    assert reminder.completed is False


@pytest.mark.parametrize(
    "title",
    ["", "   ", "x" * 256],
)
def test_create_rejects_invalid_title(db, title):
    user = create_user(db)
    service = ReminderService(db)

    with pytest.raises(ReminderValidationError):
        service.create(user.id, title, future_time(hours=1))


@pytest.mark.parametrize(
    "remind_at",
    [
        datetime.now(timezone.utc) - timedelta(minutes=1),
        datetime.now(),
    ],
)
def test_create_rejects_past_or_timezone_naive_time(db, remind_at):
    user = create_user(db)
    service = ReminderService(db)

    with pytest.raises(ReminderValidationError):
        service.create(user.id, "Study Korean", remind_at)


def test_list_for_user_filters_and_validates_pagination(db):
    user = create_user(db)
    service = ReminderService(db)

    first = service.create(
        user.id, "First", future_time(hours=1)
    )
    second = service.create(
        user.id, "Second", future_time(hours=2)
    )
    service.set_completed(user.id, second.id)

    assert [item.id for item in service.list_for_user(user.id)] == [
        first.id, second.id
    ]
    assert [
        item.id
        for item in service.list_for_user(user.id, completed=True)
    ] == [second.id]

    with pytest.raises(ReminderValidationError):
        service.list_for_user(user.id, limit=0)

    with pytest.raises(ReminderValidationError):
        service.list_for_user(user.id, offset=-1)


def test_update_requires_owner_and_future_time(db):
    owner = create_user(db)
    other_user = create_user(db)
    service = ReminderService(db)

    reminder = service.create(
        owner.id, "Original", future_time(hours=1)
    )

    with pytest.raises(ReminderNotFoundError):
        service.update(
            other_user.id,
            reminder.id,
            title="Hijacked",
            remind_at=future_time(hours=2),
        )

    updated = service.update(
        owner.id,
        reminder.id,
        title="Updated",
        remind_at=future_time(days=1),
    )

    assert updated.title == "Updated"


def test_complete_and_uncomplete_reminder(db):
    user = create_user(db)
    service = ReminderService(db)
    reminder = service.create(
        user.id, "Finish assignment", future_time(hours=1)
    )

    completed = service.set_completed(user.id, reminder.id)
    assert completed.completed is True

    reopened = service.set_completed(
        user.id, reminder.id, completed=False
    )
    assert reopened.completed is False


def test_delete_requires_owner_and_removes_reminder(db):
    owner = create_user(db)
    other_user = create_user(db)
    service = ReminderService(db)
    reminder = service.create(
        owner.id, "Delete me", future_time(hours=1)
    )

    with pytest.raises(ReminderNotFoundError):
        service.delete(other_user.id, reminder.id)

    service.delete(owner.id, reminder.id)

    with pytest.raises(ReminderNotFoundError):
        service.delete(owner.id, reminder.id)