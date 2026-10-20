from uuid import uuid4

import pytest

from app.models.user import User
from app.services.feature_preference_service import (
    FeaturePreferenceService,
    FeaturePreferenceValidationError,
)


def create_user(db) -> User:
    user = User(
        email=f"{uuid4().hex}@example.com",
        password_hash="test-hash",
        display_name="Feature Preference Service Test",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_replace_normalizes_preferences(db):
    user = create_user(db)
    service = FeaturePreferenceService(db)

    records = service.replace_for_user(
        user.id,
        {
            " daily_drop ": " high ",
            "games": "medium",
        },
    )

    assert {
        item.feature: item.preference
        for item in records
    } == {
        "daily_drop": "high",
        "games": "medium",
    }


def test_get_preferences_for_user(db):
    user = create_user(db)
    service = FeaturePreferenceService(db)

    service.replace_for_user(
        user.id,
        {"daily_drop": "high"},
    )

    records = service.get_for_user(user.id)

    assert {
        item.feature: item.preference
        for item in records
    } == {"daily_drop": "high"}


@pytest.mark.parametrize(
    "preferences",
    [
        None,
        [],
        "daily_drop",
        {1: "high"},
        {"   ": "high"},
        {"x" * 101: "high"},
        {"daily_drop": 1},
        {"daily_drop": "   "},
        {"daily_drop": "x" * 51},
    ],
)
def test_replace_rejects_invalid_preferences(db, preferences):
    user = create_user(db)
    service = FeaturePreferenceService(db)

    with pytest.raises(FeaturePreferenceValidationError):
        service.replace_for_user(user.id, preferences)


def test_invalid_replacement_preserves_existing_preferences(db):
    user = create_user(db)
    service = FeaturePreferenceService(db)

    service.replace_for_user(
        user.id,
        {"daily_drop": "high"},
    )

    with pytest.raises(FeaturePreferenceValidationError):
        service.replace_for_user(
            user.id,
            {
                "games": "medium",
                "": "low",
            },
        )

    assert {
        item.feature: item.preference
        for item in service.get_for_user(user.id)
    } == {"daily_drop": "high"}


def test_replace_with_empty_dict_clears_preferences(db):
    user = create_user(db)
    service = FeaturePreferenceService(db)

    service.replace_for_user(
        user.id,
        {"daily_drop": "high"},
    )

    assert service.replace_for_user(user.id, {}) == []
    assert service.get_for_user(user.id) == []


def test_preferences_remain_isolated_between_users(db):
    user = create_user(db)
    other_user = create_user(db)
    service = FeaturePreferenceService(db)

    service.replace_for_user(
        user.id,
        {"daily_drop": "high"},
    )
    service.replace_for_user(
        other_user.id,
        {"games": "low"},
    )

    assert {
        item.feature: item.preference
        for item in service.get_for_user(user.id)
    } == {"daily_drop": "high"}

    assert {
        item.feature: item.preference
        for item in service.get_for_user(other_user.id)
    } == {"games": "low"}