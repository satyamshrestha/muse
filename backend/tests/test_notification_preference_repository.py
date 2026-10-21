from uuid import uuid4

from app.models.notification_preference import NotificationPreference
from app.models.user import User
from app.repositories.notification_preference_repository import (
    NotificationPreferenceRepository,
)


def create_user(db):
    user = User(
        email=f"{uuid4().hex}@example.com",
        password_hash="test-hash",
        display_name="Test User",
    )
    db.add(user)
    db.flush()
    return user


def test_get_by_user_id_returns_none_when_preferences_do_not_exist(db):
    user = create_user(db)
    repository = NotificationPreferenceRepository(db)

    result = repository.get_by_user_id(user.id)

    assert result is None


def test_upsert_creates_notification_preferences(db):
    user = create_user(db)
    repository = NotificationPreferenceRepository(db)

    result = repository.upsert(
        user_id=user.id,
        enabled=False,
        daily_drop_enabled=True,
        group_activity_enabled=False,
        quiet_hours_start=22,
        quiet_hours_end=7,
    )

    assert result.id is not None
    assert result.user_id == user.id
    assert result.enabled is False
    assert result.daily_drop_enabled is True
    assert result.group_activity_enabled is False
    assert result.quiet_hours_start == 22
    assert result.quiet_hours_end == 7

    persisted = db.get(NotificationPreference, result.id)
    assert persisted is result


def test_get_by_user_id_returns_saved_preferences(db):
    user = create_user(db)
    repository = NotificationPreferenceRepository(db)

    created = repository.upsert(
        user_id=user.id,
        enabled=True,
        daily_drop_enabled=False,
        group_activity_enabled=True,
        quiet_hours_start=23,
        quiet_hours_end=6,
    )

    result = repository.get_by_user_id(user.id)

    assert result is not None
    assert result.id == created.id
    assert result.enabled is True
    assert result.daily_drop_enabled is False
    assert result.group_activity_enabled is True
    assert result.quiet_hours_start == 23
    assert result.quiet_hours_end == 6


def test_upsert_updates_existing_preferences_without_duplicates(db):
    user = create_user(db)
    repository = NotificationPreferenceRepository(db)

    original = repository.upsert(
        user_id=user.id,
        enabled=True,
        daily_drop_enabled=True,
        group_activity_enabled=True,
        quiet_hours_start=22,
        quiet_hours_end=7,
    )

    updated = repository.upsert(
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


def test_notification_preferences_are_isolated_between_users(db):
    first_user = create_user(db)
    second_user = create_user(db)
    repository = NotificationPreferenceRepository(db)

    repository.upsert(
        user_id=first_user.id,
        enabled=False,
        daily_drop_enabled=True,
        group_activity_enabled=False,
    )
    repository.upsert(
        user_id=second_user.id,
        enabled=True,
        daily_drop_enabled=False,
        group_activity_enabled=True,
    )

    first_preferences = repository.get_by_user_id(first_user.id)
    second_preferences = repository.get_by_user_id(second_user.id)

    assert first_preferences is not None
    assert second_preferences is not None
    assert first_preferences.user_id == first_user.id
    assert second_preferences.user_id == second_user.id
    assert first_preferences.enabled is False
    assert second_preferences.enabled is True
    assert first_preferences.daily_drop_enabled is True
    assert second_preferences.daily_drop_enabled is False