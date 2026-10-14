from uuid import uuid4

from app.auth.jwt import get_current_user_id
from app.main import app
from app.models.notification import Notification
from app.models.user import User


def create_user(db) -> User:
    user = User(
        email=f"{uuid4().hex}@example.com",
        password_hash="test-hash",
        display_name="Notification API Test",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_notification(db, user_id, title: str) -> Notification:
    notification = Notification(
        user_id=user_id,
        notification_type="group_activity",
        title=title,
        body="Test notification",
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def test_notification_api_lifecycle(client, db):
    owner = create_user(db)
    other_user = create_user(db)

    first = create_notification(db, owner.id, "First notification")
    create_notification(db, owner.id, "Second notification")
    create_notification(db, other_user.id, "Private notification")

    app.dependency_overrides[get_current_user_id] = lambda: owner.id

    try:
        response = client.get("/api/v1/notifications")
        assert response.status_code == 200
        payload = response.json()
        assert len(payload["items"]) == 2
        assert payload["limit"] == 20
        assert all(
            item["title"] != "Private notification"
            for item in payload["items"]
        )

        response = client.get(
            "/api/v1/notifications",
            params={"limit": 1, "offset": 0},
        )
        assert response.status_code == 200
        assert len(response.json()["items"]) == 1

        response = client.get("/api/v1/notifications/unread-count")
        assert response.status_code == 200
        assert response.json()["unread_count"] == 2

        response = client.patch(
            f"/api/v1/notifications/{first.id}/read"
        )
        assert response.status_code == 200
        assert response.json()["read_at"] is not None

        response = client.get("/api/v1/notifications/unread-count")
        assert response.json()["unread_count"] == 1

        response = client.post("/api/v1/notifications/read-all")
        assert response.status_code == 200
        assert response.json()["updated_count"] == 1

        response = client.get("/api/v1/notifications/unread-count")
        assert response.json()["unread_count"] == 0

        response = client.patch(
            f"/api/v1/notifications/{first.id}/read"
        )
        assert response.status_code == 200

        app.dependency_overrides[get_current_user_id] = (
            lambda: other_user.id
        )
        response = client.patch(
            f"/api/v1/notifications/{first.id}/read"
        )
        assert response.status_code == 404

    finally:
        app.dependency_overrides.pop(get_current_user_id, None)


def test_notification_list_validates_pagination(client, db):
    user = create_user(db)
    app.dependency_overrides[get_current_user_id] = lambda: user.id

    try:
        response = client.get(
            "/api/v1/notifications",
            params={"limit": 101},
        )
        assert response.status_code == 422

        response = client.get(
            "/api/v1/notifications",
            params={"offset": -1},
        )
        assert response.status_code == 422
    finally:
        app.dependency_overrides.pop(get_current_user_id, None)