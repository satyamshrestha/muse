from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.auth.jwt import get_current_user_id
from app.models.user import User
from app.services.dependencies import get_reminder_service
from app.services.reminder_service import ReminderService


def test_reminder_api_crud(db, client):
    user = User(
        email=f"{uuid4().hex}@example.com",
        password_hash="test-hash",
        display_name="Reminder API Test",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    client.app.dependency_overrides[get_current_user_id] = (
        lambda: user.id
    )
    client.app.dependency_overrides[get_reminder_service] = (
        lambda: ReminderService(db)
    )

    try:
        payload = {
            "title": "  Study Korean  ",
            "remind_at": (
                datetime.now(timezone.utc) + timedelta(hours=2)
            ).isoformat(),
        }

        created_response = client.post(
            "/api/v1/reminders",
            json=payload,
        )
        assert created_response.status_code == 201
        created = created_response.json()
        assert created["title"] == "Study Korean"
        reminder_id = created["id"]

        list_response = client.get("/api/v1/reminders")
        assert list_response.status_code == 200
        assert any(
            item["id"] == reminder_id
            for item in list_response.json()
        )

        completion_response = client.patch(
            f"/api/v1/reminders/{reminder_id}/completion",
            json={"completed": True},
        )
        assert completion_response.status_code == 200
        assert completion_response.json()["completed"] is True

        update_response = client.patch(
            f"/api/v1/reminders/{reminder_id}",
            json={
                "title": "Updated reminder",
                "remind_at": (
                    datetime.now(timezone.utc) + timedelta(days=1)
                ).isoformat(),
            },
        )
        assert update_response.status_code == 200
        assert update_response.json()["title"] == "Updated reminder"

        delete_response = client.delete(
            f"/api/v1/reminders/{reminder_id}"
        )
        assert delete_response.status_code == 204

        missing_response = client.patch(
            f"/api/v1/reminders/{reminder_id}/completion",
            json={"completed": False},
        )
        assert missing_response.status_code == 404

    finally:
        client.app.dependency_overrides.pop(
            get_current_user_id, None
        )
        client.app.dependency_overrides.pop(
            get_reminder_service, None
        )