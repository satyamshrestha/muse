from uuid import uuid4

from app.models.user import User
from app.repositories.feature_preference_repository import (
    FeaturePreferenceRepository,
)


def create_user(db) -> User:
    user = User(
        email=f"{uuid4().hex}@example.com",
        password_hash="test-hash",
        display_name="Feature Preference Test",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_replace_and_get_feature_preferences(db):
    user = create_user(db)
    repository = FeaturePreferenceRepository(db)

    records = repository.replace_for_user(
        user.id,
        {
            "daily_drop": "high",
            "games": "medium",
            "recommendations": "low",
        },
    )
    db.commit()

    assert len(records) == 3

    preferences = repository.get_by_user_id(user.id)
    assert {
        item.feature: item.preference
        for item in preferences
    } == {
        "daily_drop": "high",
        "games": "medium",
        "recommendations": "low",
    }


def test_feature_preferences_are_scoped_to_user(db):
    user = create_user(db)
    other_user = create_user(db)
    repository = FeaturePreferenceRepository(db)

    repository.replace_for_user(
        user.id,
        {"daily_drop": "high"},
    )
    repository.replace_for_user(
        other_user.id,
        {"games": "low"},
    )
    db.commit()

    assert {
        item.feature: item.preference
        for item in repository.get_by_user_id(user.id)
    } == {"daily_drop": "high"}

    assert {
        item.feature: item.preference
        for item in repository.get_by_user_id(other_user.id)
    } == {"games": "low"}


def test_replace_removes_previous_feature_preferences(db):
    user = create_user(db)
    repository = FeaturePreferenceRepository(db)

    repository.replace_for_user(
        user.id,
        {
            "daily_drop": "high",
            "games": "medium",
        },
    )
    db.commit()

    repository.replace_for_user(
        user.id,
        {"recommendations": "low"},
    )
    db.commit()

    assert {
        item.feature: item.preference
        for item in repository.get_by_user_id(user.id)
    } == {"recommendations": "low"}


def test_replace_with_empty_dict_clears_feature_preferences(db):
    user = create_user(db)
    repository = FeaturePreferenceRepository(db)

    repository.replace_for_user(
        user.id,
        {
            "daily_drop": "high",
            "games": "medium",
        },
    )
    db.commit()

    repository.replace_for_user(user.id, {})
    db.commit()

    assert repository.get_by_user_id(user.id) == []