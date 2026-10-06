from uuid import uuid4

from app.models.feature_preference import FeaturePreference
from app.models.notification_preference import NotificationPreference
from app.models.user_interest import UserInterest
from app.models.user_preference import UserPreference
from app.models.user import User
from app.services.personalization_service import PersonalizationService


def test_save_personalization(db):
    user = User(
        email=f"{uuid4()}@example.com",
        password_hash="hashed-password",
        display_name="Test User",
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    service = PersonalizationService(
        user_repository=__import__(
            "app.repositories.user_repository",
            fromlist=["UserRepository"],
        ).UserRepository(db),
        invitation_service=None,
        configuration_repository=None,
        user_interest_repository=__import__(
            "app.repositories.user_interest_repository",
            fromlist=["UserInterestRepository"],
        ).UserInterestRepository(db),
        user_preference_repository=__import__(
            "app.repositories.user_preference_repository",
            fromlist=["UserPreferenceRepository"],
        ).UserPreferenceRepository(db),
        feature_preference_repository=__import__(
            "app.repositories.feature_preference_repository",
            fromlist=["FeaturePreferenceRepository"],
        ).FeaturePreferenceRepository(db),
        notification_preference_repository=__import__(
            "app.repositories.notification_preference_repository",
            fromlist=["NotificationPreferenceRepository"],
        ).NotificationPreferenceRepository(db),
    )

    service.save_personalization(
        user_id=user.id,
        interests=["coding", "music"],
        preferences={
            "theme": "dark",
            "recommendation_style": "balanced",
        },
        feature_preferences={
            "daily_drop": "high",
            "games": "medium",
        },
        notification_enabled=True,
        daily_drop_enabled=True,
        group_activity_enabled=False,
        quiet_hours_start=23,
        quiet_hours_end=8,
    )

    interests = db.query(UserInterest).filter(
        UserInterest.user_id == user.id
    ).all()

    preferences = db.query(UserPreference).filter(
        UserPreference.user_id == user.id
    ).all()

    feature_preferences = db.query(FeaturePreference).filter(
        FeaturePreference.user_id == user.id
    ).all()

    notification = db.query(NotificationPreference).filter(
        NotificationPreference.user_id == user.id
    ).one()

    assert {item.interest for item in interests} == {
        "coding",
        "music",
    }

    assert {
        item.key: item.value
        for item in preferences
    } == {
        "theme": "dark",
        "recommendation_style": "balanced",
    }

    assert {
        item.feature: item.preference
        for item in feature_preferences
    } == {
        "daily_drop": "high",
        "games": "medium",
    }

    assert notification.enabled is True
    assert notification.daily_drop_enabled is True
    assert notification.group_activity_enabled is False
    assert notification.quiet_hours_start == 23
    assert notification.quiet_hours_end == 8