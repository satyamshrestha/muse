from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.auth.jwt import get_current_user_id
from app.models.user import User
from app.services.dependencies import get_reminder_service
from app.services.reminder_service import ReminderService


def setup_reminder_api(db, client):
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

    return user


def test_reminder_api_crud(db, client):
    user = setup_reminder_api(db, client)

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


def test_reminder_api_filtering_and_pagination(db, client):
    user = setup_reminder_api(db, client)

    try:
        service = ReminderService(db)
        now = datetime.now(timezone.utc)

        first = service.create(
            user.id, "First", now + timedelta(hours=1)
        )
        second = service.create(
            user.id, "Second", now + timedelta(hours=2)
        )
        third = service.create(
            user.id, "Third", now + timedelta(hours=3)
        )
        service.set_completed(user.id, second.id)

        all_response = client.get("/api/v1/reminders")
        assert all_response.status_code == 200
        assert len(all_response.json()) == 3

        completed_response = client.get(
            "/api/v1/reminders",
            params={"completed": "true"},
        )
        assert completed_response.status_code == 200
        assert [
            item["id"] for item in completed_response.json()
        ] == [str(second.id)]

        incomplete_response = client.get(
            "/api/v1/reminders",
            params={"completed": "false"},
        )
        assert incomplete_response.status_code == 200
        assert {
            item["id"] for item in incomplete_response.json()
        } == {str(first.id), str(third.id)}

        page_response = client.get(
            "/api/v1/reminders",
            params={"limit": 1, "offset": 1},
        )
        assert page_response.status_code == 200
        assert [
            item["id"] for item in page_response.json()
        ] == [str(second.id)]

    finally:
        client.app.dependency_overrides.pop(
            get_current_user_id, None
        )
        client.app.dependency_overrides.pop(
            get_reminder_service, None
        )


def test_reminder_api_rejects_invalid_timestamps(db, client):
    setup_reminder_api(db, client)

    try:
        response = client.post(
            "/api/v1/reminders",
            json={
                "title": "Study Korean",
                "remind_at": datetime.now().isoformat(),
            },
        )

        assert response.status_code == 422

    finally:
        client.app.dependency_overrides.pop(
            get_current_user_id, None
        )
        client.app.dependency_overrides.pop(
            get_reminder_service, None
        )


def test_reminder_api_rejects_invalid_completion_payload(db, client):
    setup_reminder_api(db, client)

    try:
        invalid_values = [
            "not-a-boolean",
            [],
            {},
        ]

        for invalid_value in invalid_values:
            response = client.patch(
                "/api/v1/reminders/00000000-0000-0000-0000-000000000001/completion",
                json={"completed": invalid_value},
            )
            assert response.status_code == 422

    finally:
        client.app.dependency_overrides.pop(
            get_current_user_id, None
        )
        client.app.dependency_overrides.pop(
            get_reminder_service, None
        )


def test_reminder_api_rejects_invalid_pagination(db, client):
    setup_reminder_api(db, client)

    try:
        invalid_queries = [
            {"limit": 0},
            {"limit": 101},
            {"offset": -1},
        ]

        for params in invalid_queries:
            response = client.get(
                "/api/v1/reminders",
                params=params,
            )
            assert response.status_code == 422

    finally:
        client.app.dependency_overrides.pop(
            get_current_user_id, None
        )
        client.app.dependency_overrides.pop(
            get_reminder_service, None
        )