from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.models.reminder import Reminder
from app.models.user import User
from app.repositories.reminder_repository import ReminderRepository


def create_user(db) -> User:
    user = User(
        email=f"{uuid4().hex}@example.com",
        password_hash="test-hash",
        display_name="Reminder Repository Test",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_reminder(
    repository: ReminderRepository,
    user_id,
    title: str,
    remind_at: datetime,
) -> Reminder:
    return repository.create(
        user_id=user_id,
        title=title,
        remind_at=remind_at,
    )


def test_create_reminder(db):
    user = create_user(db)
    repository = ReminderRepository(db)
    remind_at = datetime.now(timezone.utc) + timedelta(hours=1)

    reminder = create_reminder(
        repository, user.id, "Study Korean", remind_at
    )
    db.commit()
    db.refresh(reminder)

    assert reminder.id is not None
    assert reminder.user_id == user.id
    assert reminder.title == "Study Korean"
    assert reminder.completed is False


def test_get_by_id_requires_matching_owner(db):
    owner = create_user(db)
    other_user = create_user(db)
    repository = ReminderRepository(db)

    reminder = create_reminder(
        repository,
        owner.id,
        "Private reminder",
        datetime.now(timezone.utc) + timedelta(hours=1),
    )
    db.commit()

    assert repository.get_by_id_for_user(
        reminder.id, owner.id
    ) is not None
    assert repository.get_by_id_for_user(
        reminder.id, other_user.id
    ) is None


def test_list_by_user_is_scoped_and_ordered(db):
    user = create_user(db)
    other_user = create_user(db)
    repository = ReminderRepository(db)
    now = datetime.now(timezone.utc)

    later = create_reminder(
        repository, user.id, "Later", now + timedelta(hours=2)
    )
    earlier = create_reminder(
        repository, user.id, "Earlier", now + timedelta(hours=1)
    )
    create_reminder(
        repository, other_user.id, "Other user's reminder",
        now + timedelta(minutes=30),
    )
    db.commit()

    reminders = repository.list_by_user(user.id)

    assert [item.id for item in reminders] == [
        earlier.id, later.id
    ]
    assert all(item.user_id == user.id for item in reminders)


def test_list_supports_pagination_and_completion_filter(db):
    user = create_user(db)
    repository = ReminderRepository(db)
    now = datetime.now(timezone.utc)

    first = create_reminder(
        repository, user.id, "First", now + timedelta(hours=1)
    )
    second = create_reminder(
        repository, user.id, "Second", now + timedelta(hours=2)
    )
    create_reminder(
        repository, user.id, "Third", now + timedelta(hours=3)
    )
    db.commit()

    repository.set_completed(second, True)
    db.commit()

    page = repository.list_by_user(user.id, limit=1, offset=0)
    completed = repository.list_by_user(user.id, completed=True)
    incomplete = repository.list_by_user(user.id, completed=False)

    assert len(page) == 1
    assert page[0].id == first.id
    assert [item.id for item in completed] == [second.id]
    assert len(incomplete) == 2


def test_update_reminder(db):
    user = create_user(db)
    repository = ReminderRepository(db)
    reminder = create_reminder(
        repository,
        user.id,
        "Old title",
        datetime.now(timezone.utc) + timedelta(hours=1),
    )
    db.commit()

    new_time = datetime.now(timezone.utc) + timedelta(days=1)
    repository.update(
        reminder,
        title="Updated title",
        remind_at=new_time,
    )
    db.commit()
    db.refresh(reminder)

    assert reminder.title == "Updated title"
    assert reminder.remind_at == new_time


def test_set_completed_and_delete(db):
    user = create_user(db)
    repository = ReminderRepository(db)
    reminder = create_reminder(
        repository,
        user.id,
        "Finish assignment",
        datetime.now(timezone.utc) + timedelta(hours=1),
    )
    db.commit()
    reminder_id = reminder.id

    repository.set_completed(reminder, True)
    db.commit()
    assert repository.get_by_id_for_user(
        reminder_id, user.id
    ).completed is True

    repository.delete(reminder)
    db.commit()

    assert repository.get_by_id_for_user(
        reminder_id, user.id
    ) is None