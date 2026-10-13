from uuid import uuid4

from app.auth.jwt import get_current_user_id
from app.main import app
from app.models.user import User


def create_user(db) -> User:
    user = User(
        email=f"{uuid4().hex}@example.com",
        password_hash="test-hash",
        display_name="Device API Test",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_device_lifecycle_api(client, db):
    owner = create_user(db)
    other_user = create_user(db)

    app.dependency_overrides[get_current_user_id] = lambda: owner.id

    try:
        # Register a device.
        response = client.post(
            "/api/v1/devices",
            json={
                "device_token": "api-device-token-001",
                "platform": "android",
            },
        )

        assert response.status_code == 201
        created = response.json()
        device_id = created["id"]

        assert created["platform"] == "android"
        assert "device_token" not in created

        # Re-registering the same token for the same user is idempotent.
        response = client.post(
            "/api/v1/devices",
            json={
                "device_token": "api-device-token-001",
                "platform": "ios",
            },
        )

        assert response.status_code == 201
        assert response.json()["id"] == device_id
        assert response.json()["platform"] == "ios"

        # List only this user's devices.
        response = client.get("/api/v1/devices")

        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["id"] == device_id

        # Update the platform.
        response = client.patch(
            f"/api/v1/devices/{device_id}",
            json={"platform": "android"},
        )

        assert response.status_code == 200
        assert response.json()["platform"] == "android"

        # A different user cannot claim the same token.
        app.dependency_overrides[get_current_user_id] = (
            lambda: other_user.id
        )

        response = client.post(
            "/api/v1/devices",
            json={
                "device_token": "api-device-token-001",
                "platform": "ios",
            },
        )

        assert response.status_code == 409

        # Nor can the other user update or delete the owner's device.
        response = client.patch(
            f"/api/v1/devices/{device_id}",
            json={"platform": "ios"},
        )
        assert response.status_code == 404

        response = client.delete(
            f"/api/v1/devices/{device_id}"
        )
        assert response.status_code == 404

        # The owner can still delete it.
        app.dependency_overrides[get_current_user_id] = (
            lambda: owner.id
        )

        response = client.delete(
            f"/api/v1/devices/{device_id}"
        )
        assert response.status_code == 204

        response = client.get("/api/v1/devices")
        assert response.status_code == 200
        assert response.json() == []

    finally:
        app.dependency_overrides.pop(
            get_current_user_id,
            None,
        )