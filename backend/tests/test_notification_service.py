from uuid import uuid4

import pytest

from app.models.notification import Notification
from app.models.notification_preference import NotificationPreference
from app.models.user import User
from app.repositories.notification_preference_repository import (
    NotificationPreferenceRepository,
)
from app.repositories.notification_repository import NotificationRepository
from app.services.notification_service import (
    NotificationNotFoundError,
    NotificationPreferenceError,
    NotificationService,
)


def create_user(db) -> User:
    user = User(
        email=f"{uuid4().hex}@example.com",
        password_hash="test-hash",
        display_name="Notification Service Test",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def build_service(db) -> NotificationService:
    return NotificationService(
        repository=NotificationRepository(db),
        preference_repository=NotificationPreferenceRepository(db),
    )


def set_preferences(db, user_id, **overrides):
    values = {
        "enabled": True,
        "daily_drop_enabled": True,
        "group_activity_enabled": True,
        "quiet_hours_start": None,
        "quiet_hours_end": None,
    }
    values.update(overrides)
    db.add(NotificationPreference(user_id=user_id, **values))
    db.commit()


def test_create_notification(db):
    user = create_user(db)
    service = build_service(db)

    notification = service.create_for_user(
        user_id=user.id,
        notification_type="group_activity",
        title="New group activity",
        body="Your group has a new update.",
    )

    assert notification is not None
    assert notification.user_id == user.id
    assert notification.read_at is None


def test_global_preference_disables_creation(db):
    user = create_user(db)
    set_preferences(db, user.id, enabled=False)
    service = build_service(db)

    notification = service.create_for_user(
        user.id,
        "group_activity",
        "Group update",
    )

    assert notification is None
    assert service.unread_count(user.id) == 0


def test_category_preference_disables_creation(db):
    user = create_user(db)
    set_preferences(db, user.id, daily_drop_enabled=False)
    service = build_service(db)

    notification = service.create_for_user(
        user.id,
        "daily_drop",
        "Daily drop",
    )

    assert notification is None


def test_unrelated_category_remains_enabled(db):
    user = create_user(db)
    set_preferences(db, user.id, daily_drop_enabled=False)
    service = build_service(db)

    notification = service.create_for_user(
        user.id,
        "group_activity",
        "Group update",
    )

    assert notification is not None


def test_list_and_unread_count_are_user_scoped(db):
    user = create_user(db)
    other_user = create_user(db)
    service = build_service(db)

    service.create_for_user(user.id, "group_activity", "First")
    service.create_for_user(user.id, "group_activity", "Second")
    service.create_for_user(other_user.id, "group_activity", "Other")

    assert len(service.list_for_user(user.id)) == 2
    assert service.unread_count(user.id) == 2


def test_mark_read_requires_ownership(db):
    owner = create_user(db)
    other_user = create_user(db)
    service = build_service(db)

    notification = service.create_for_user(
        owner.id,
        "group_activity",
        "Owner notification",
    )

    with pytest.raises(NotificationNotFoundError):
        service.mark_read(other_user.id, notification.id)

    assert service.unread_count(owner.id) == 1


def test_mark_read_and_mark_all_read(db):
    user = create_user(db)
    service = build_service(db)

    first = service.create_for_user(user.id, "group_activity", "First")
    service.create_for_user(user.id, "group_activity", "Second")

    updated = service.mark_read(user.id, first.id)
    assert updated.read_at is not None
    assert service.unread_count(user.id) == 1

    assert service.mark_all_read(user.id) == 1
    assert service.unread_count(user.id) == 0


@pytest.mark.parametrize(
    ("start", "end", "hour", "expected"),
    [
        (22, 6, 23, True),
        (22, 6, 4, True),
        (22, 6, 12, False),
        (9, 17, 9, True),
        (9, 17, 17, False),
        (None, None, 12, False),
        (8, 8, 8, False),
    ],
)
def test_quiet_hours_boundaries(
    start,
    end,
    hour,
    expected,
):
    preference = NotificationPreference(
        user_id=uuid4(),
        enabled=True,
        daily_drop_enabled=True,
        group_activity_enabled=True,
        quiet_hours_start=start,
        quiet_hours_end=end,
    )

    assert (
        NotificationService.is_within_quiet_hours(preference, hour)
        is expected
    )


@pytest.mark.parametrize(
    ("start", "end"),
    [
        (-1, 5),
        (5, 24),
        (5, None),
        (None, 5),
    ],
)
def test_invalid_quiet_hours_are_rejected(start, end):
    with pytest.raises(NotificationPreferenceError):
        NotificationService.validate_quiet_hours(start, end)