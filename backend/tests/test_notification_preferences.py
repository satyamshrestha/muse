from uuid import uuid4

from app.auth.jwt import get_current_user_id
from app.main import app
from app.models.notification_preference import NotificationPreference
from app.models.user import User


def create_user(db) -> User:
    user = User(
        email=f"{uuid4().hex}@example.com",
        password_hash="test-hash",
        display_name="Notification Preference API Test",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_notification_preference_api_requires_authentication(client):
    response = client.get("/api/v1/notification-preferences")
    assert response.status_code in (401, 403)

    response = client.put(
        "/api/v1/notification-preferences",
        json={"enabled": True},
    )
    assert response.status_code in (401, 403)


def test_notification_preference_api_lifecycle(client, db):
    owner = create_user(db)
    other_user = create_user(db)

    app.dependency_overrides[get_current_user_id] = lambda: owner.id

    try:
        response = client.get("/api/v1/notification-preferences")
        assert response.status_code == 200
        assert response.json() is None

        payload = {
            "enabled": False,
            "daily_drop_enabled": True,
            "group_activity_enabled": False,
            "quiet_hours_start": 22,
            "quiet_hours_end": 7,
        }
        response = client.put(
            "/api/v1/notification-preferences",
            json=payload,
        )
        assert response.status_code == 200
        saved = response.json()
        assert saved["user_id"] == str(owner.id)
        assert saved["enabled"] is False
        assert saved["daily_drop_enabled"] is True
        assert saved["group_activity_enabled"] is False
        assert saved["quiet_hours_start"] == 22
        assert saved["quiet_hours_end"] == 7

        response = client.get("/api/v1/notification-preferences")
        assert response.status_code == 200
        assert response.json()["id"] == saved["id"]

        updated_payload = {
            "enabled": True,
            "daily_drop_enabled": False,
            "group_activity_enabled": True,
            "quiet_hours_start": None,
            "quiet_hours_end": None,
        }
        response = client.put(
            "/api/v1/notification-preferences",
            json=updated_payload,
        )
        assert response.status_code == 200
        updated = response.json()
        assert updated["id"] == saved["id"]
        assert updated["enabled"] is True
        assert updated["daily_drop_enabled"] is False
        assert updated["quiet_hours_start"] is None
        assert updated["quiet_hours_end"] is None

        assert (
            db.query(NotificationPreference)
            .filter(NotificationPreference.user_id == owner.id)
            .count()
            == 1
        )

        app.dependency_overrides[get_current_user_id] = (
            lambda: other_user.id
        )
        response = client.get("/api/v1/notification-preferences")
        assert response.status_code == 200
        assert response.json() is None

    finally:
        app.dependency_overrides.pop(get_current_user_id, None)


def test_notification_preference_api_rejects_invalid_quiet_hours(
    client, db
):
    user = create_user(db)
    app.dependency_overrides[get_current_user_id] = lambda: user.id

    try:
        valid_payload = {
            "enabled": True,
            "daily_drop_enabled": True,
            "group_activity_enabled": True,
            "quiet_hours_start": 22,
            "quiet_hours_end": 7,
        }
        response = client.put(
            "/api/v1/notification-preferences",
            json=valid_payload,
        )
        assert response.status_code == 200
        original_id = response.json()["id"]

        invalid_payloads = [
            {"quiet_hours_start": -1, "quiet_hours_end": 7},
            {"quiet_hours_start": 22, "quiet_hours_end": 24},
            {"quiet_hours_start": 22, "quiet_hours_end": None},
            {"quiet_hours_start": None, "quiet_hours_end": 7},
        ]

        for invalid_hours in invalid_payloads:
            payload = {
                "enabled": False,
                "daily_drop_enabled": False,
                "group_activity_enabled": False,
                **invalid_hours,
            }
            response = client.put(
                "/api/v1/notification-preferences",
                json=payload,
            )
            assert response.status_code == 422

        response = client.get("/api/v1/notification-preferences")
        assert response.status_code == 200
        assert response.json()["id"] == original_id
        assert response.json()["enabled"] is True

    finally:
        app.dependency_overrides.pop(get_current_user_id, None)