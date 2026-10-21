import pytest
from uuid import uuid4

from app.models.notification_preference import NotificationPreference
from app.models.user import User
from app.services.notification_preference_service import (
    NotificationPreferenceService,
)
from app.services.notification_service import NotificationPreferenceError


def create_user(db):
    user = User(
        email=f"{uuid4().hex}@example.com",
        password_hash="test-hash",
        display_name="Test User",
    )
    db.add(user)
    db.flush()
    return user


def test_get_for_user_returns_none_when_preferences_do_not_exist(db):
    user = create_user(db)
    service = NotificationPreferenceService(db)

    assert service.get_for_user(user.id) is None


def test_update_for_user_creates_preferences(db):
    user = create_user(db)
    service = NotificationPreferenceService(db)

    result = service.update_for_user(
        user_id=user.id,
        enabled=False,
        daily_drop_enabled=True,
        group_activity_enabled=False,
        quiet_hours_start=22,
        quiet_hours_end=7,
    )

    assert result.user_id == user.id
    assert result.enabled is False
    assert result.daily_drop_enabled is True
    assert result.group_activity_enabled is False
    assert result.quiet_hours_start == 22
    assert result.quiet_hours_end == 7
    assert result.id is not None


def test_update_for_user_updates_existing_preferences(db):
    user = create_user(db)
    service = NotificationPreferenceService(db)

    original = service.update_for_user(
        user_id=user.id,
        enabled=True,
        daily_drop_enabled=True,
        group_activity_enabled=True,
        quiet_hours_start=22,
        quiet_hours_end=7,
    )

    updated = service.update_for_user(
        user_id=user.id,
        enabled=False,
        daily_drop_enabled=False,
        group_activity_enabled=True,
        quiet_hours_start=None,
        quiet_hours_end=None,
    )

    assert updated.id == original.id
    assert updated.enabled is False
    assert updated.daily_drop_enabled is False
    assert updated.group_activity_enabled is True
    assert updated.quiet_hours_start is None
    assert updated.quiet_hours_end is None

    preferences = (
        db.query(NotificationPreference)
        .filter(NotificationPreference.user_id == user.id)
        .all()
    )
    assert len(preferences) == 1


@pytest.mark.parametrize(
    ("quiet_hours_start", "quiet_hours_end"),
    [
        (-1, 7),
        (22, 24),
        (None, 7),
        (22, None),
    ],
)
def test_update_for_user_rejects_invalid_quiet_hours(
    db,
    quiet_hours_start,
    quiet_hours_end,
):
    user = create_user(db)
    service = NotificationPreferenceService(db)

    with pytest.raises(NotificationPreferenceError):
        service.update_for_user(
            user_id=user.id,
            enabled=True,
            daily_drop_enabled=True,
            group_activity_enabled=True,
            quiet_hours_start=quiet_hours_start,
            quiet_hours_end=quiet_hours_end,
        )

    assert service.get_for_user(user.id) is None


def test_invalid_update_preserves_existing_preferences(db):
    user = create_user(db)
    service = NotificationPreferenceService(db)

    original = service.update_for_user(
        user_id=user.id,
        enabled=True,
        daily_drop_enabled=False,
        group_activity_enabled=True,
        quiet_hours_start=22,
        quiet_hours_end=7,
    )

    with pytest.raises(NotificationPreferenceError):
        service.update_for_user(
            user_id=user.id,
            enabled=False,
            daily_drop_enabled=True,
            group_activity_enabled=False,
            quiet_hours_start=22,
            quiet_hours_end=None,
        )

    current = service.get_for_user(user.id)

    assert current is not None
    assert current.id == original.id
    assert current.enabled is True
    assert current.daily_drop_enabled is False
    assert current.group_activity_enabled is True
    assert current.quiet_hours_start == 22
    assert current.quiet_hours_end == 7


def test_preferences_are_isolated_between_users(db):
    first_user = create_user(db)
    second_user = create_user(db)
    service = NotificationPreferenceService(db)

    service.update_for_user(
        user_id=first_user.id,
        enabled=False,
        daily_drop_enabled=True,
        group_activity_enabled=False,
    )
    service.update_for_user(
        user_id=second_user.id,
        enabled=True,
        daily_drop_enabled=False,
        group_activity_enabled=True,
    )

    first = service.get_for_user(first_user.id)
    second = service.get_for_user(second_user.id)

    assert first is not None
    assert second is not None
    assert first.enabled is False
    assert second.enabled is True
    assert first.daily_drop_enabled is True
    assert second.daily_drop_enabled is False