from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.models.base_configuration import BaseConfiguration
from app.models.feature_preference import FeaturePreference
from app.models.invitation_code import InvitationCode
from app.models.notification_preference import NotificationPreference
from app.models.user import User
from app.models.user_interest import UserInterest
from app.models.user_preference import UserPreference
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

    notification = db.query(
        NotificationPreference
    ).filter(
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


def test_update_personalization_endpoint(client):
    signup_response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "personalization@example.com",
            "password": "Password123!",
            "display_name": "Personalization User",
        },
    )

    assert signup_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "personalization@example.com",
            "password": "Password123!",
        },
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    response = client.put(
        "/api/v1/personalization",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
        json={
            "interests": [
                "coding",
                "music",
            ],
            "preferences": {
                "theme": "dark",
                "recommendation_style": "balanced",
            },
            "feature_preferences": {
                "daily_drop": "high",
                "games": "medium",
            },
            "notifications": {
                "enabled": True,
                "daily_drop_enabled": True,
                "group_activity_enabled": False,
                "quiet_hours_start": 23,
                "quiet_hours_end": 8,
            },
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Personalization updated successfully",
    }


def test_complete_onboarding_flow(client, db):
    configuration = BaseConfiguration(
        name=f"test-config-{uuid4()}",
        interests=["music", "movies"],
        preferences={
            "recommendation_style": "balanced",
        },
    )

    db.add(configuration)
    db.flush()

    invitation_code = InvitationCode(
        code=f"TEST-{uuid4()}",
        configuration_key=configuration.name,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )

    db.add(invitation_code)
    db.commit()

    email = f"{uuid4()}@example.com"
    password = "Password123!"

    signup_response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "password": password,
            "display_name": "Onboarding User",
        },
    )

    assert signup_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    headers = {
        "Authorization": f"Bearer {access_token}",
    }

    claim_response = client.post(
        "/api/v1/auth/claim-invitation",
        headers=headers,
        params={
            "code": invitation_code.code,
        },
    )

    assert claim_response.status_code == 200

    claim_data = claim_response.json()

    assert claim_data["configuration_id"] == str(configuration.id)
    assert claim_data["configuration_name"] == configuration.name

    personalization_response = client.put(
        "/api/v1/personalization",
        headers=headers,
        json={
            "interests": [
                "coding",
                "music",
            ],
            "preferences": {
                "theme": "dark",
                "recommendation_style": "balanced",
            },
            "feature_preferences": {
                "daily_drop": "high",
                "games": "medium",
            },
            "notifications": {
                "enabled": True,
                "daily_drop_enabled": True,
                "group_activity_enabled": False,
                "quiet_hours_start": 23,
                "quiet_hours_end": 8,
            },
        },
    )

    assert personalization_response.status_code == 200

    user = db.query(User).filter(
        User.email == email
    ).one()

    assert user.base_configuration_id == configuration.id

    interests = db.query(UserInterest).filter(
        UserInterest.user_id == user.id
    ).all()

    assert {item.interest for item in interests} == {
        "coding",
        "music",
    }

    preferences = db.query(UserPreference).filter(
        UserPreference.user_id == user.id
    ).all()

    assert {
        item.key: item.value
        for item in preferences
    } == {
        "theme": "dark",
        "recommendation_style": "balanced",
    }

    feature_preferences = db.query(
        FeaturePreference
    ).filter(
        FeaturePreference.user_id == user.id
    ).all()

    assert {
        item.feature: item.preference
        for item in feature_preferences
    } == {
        "daily_drop": "high",
        "games": "medium",
    }

    notification = db.query(
        NotificationPreference
    ).filter(
        NotificationPreference.user_id == user.id
    ).one()

    assert notification.enabled is True
    assert notification.daily_drop_enabled is True
    assert notification.group_activity_enabled is False
    assert notification.quiet_hours_start == 23
    assert notification.quiet_hours_end == 8

    db.refresh(invitation_code)

    assert invitation_code.used is True

def test_get_personalization_endpoint(client):
    email = f"{uuid4()}@example.com"
    password = "Password123!"

    signup_response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "password": password,
            "display_name": "Retrieval User",
        },
    )

    assert signup_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    headers = {
        "Authorization": f"Bearer {access_token}",
    }

    update_response = client.put(
        "/api/v1/personalization",
        headers=headers,
        json={
            "interests": [
                "coding",
                "music",
            ],
            "preferences": {
                "theme": "dark",
                "recommendation_style": "balanced",
            },
            "feature_preferences": {
                "daily_drop": "high",
                "games": "medium",
            },
            "notifications": {
                "enabled": True,
                "daily_drop_enabled": True,
                "group_activity_enabled": False,
                "quiet_hours_start": 23,
                "quiet_hours_end": 8,
            },
        },
    )

    assert update_response.status_code == 200

    response = client.get(
        "/api/v1/personalization",
        headers=headers,
    )

    assert response.status_code == 200

    assert response.json() == {
        "configuration_id": None,
        "configuration_name": None,
        "interests": [
            "coding",
            "music",
        ],
        "preferences": {
            "theme": "dark",
            "recommendation_style": "balanced",
        },
        "feature_preferences": {
            "daily_drop": "high",
            "games": "medium",
        },
        "notifications": {
            "enabled": True,
            "daily_drop_enabled": True,
            "group_activity_enabled": False,
            "quiet_hours_start": 23,
            "quiet_hours_end": 8,
        },
    }

def test_get_personalization_requires_authentication(client):
    response = client.get(
        "/api/v1/personalization"
    )

    assert response.status_code == 401


def test_update_personalization_requires_authentication(client):
    response = client.put(
        "/api/v1/personalization",
        json={
            "interests": ["coding"],
            "preferences": {},
            "feature_preferences": {},
            "notifications": {
                "enabled": True,
                "daily_drop_enabled": True,
                "group_activity_enabled": True,
            },
        },
    )

    assert response.status_code == 401


def test_update_personalization_rejects_invalid_quiet_hours(client):
    signup_response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": f"{uuid4()}@example.com",
            "password": "Password123!",
            "display_name": "Validation User",
        },
    )

    assert signup_response.status_code == 201

    email = signup_response.json()["email"]

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": "Password123!",
        },
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    response = client.put(
        "/api/v1/personalization",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
        json={
            "interests": ["coding"],
            "preferences": {},
            "feature_preferences": {},
            "notifications": {
                "enabled": True,
                "daily_drop_enabled": True,
                "group_activity_enabled": True,
                "quiet_hours_start": 24,
                "quiet_hours_end": 8,
            },
        },
    )

    assert response.status_code == 422