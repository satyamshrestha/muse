from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.auth.jwt import get_current_user_id
from app.models.user import User
from app.services.dependencies import get_mood_entry_service
from app.services.mood_entry_service import MoodEntryService


def create_user(db: Session) -> User:
    user = User(
        email=f"{uuid4().hex}@example.com",
        password_hash="test-hash",
        display_name="Mood Test User",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def set_mood_overrides(client, db: Session, user: User) -> None:
    client.app.dependency_overrides[get_current_user_id] = lambda: user.id
    client.app.dependency_overrides[get_mood_entry_service] = (
        lambda: MoodEntryService(db)
    )


def clear_mood_overrides(client) -> None:
    client.app.dependency_overrides.pop(get_current_user_id, None)
    client.app.dependency_overrides.pop(get_mood_entry_service, None)


def test_create_mood_entry(client, db: Session):
    user = create_user(db)
    set_mood_overrides(client, db, user)

    try:
        response = client.post(
            "/api/v1/moods",
            json={
                "mood": " HAPPY ",
                "intensity": 4,
                "note": "  Had a good day.  ",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] == str(user.id)
        assert data["mood"] == "happy"
        assert data["intensity"] == 4
        assert data["note"] == "Had a good day."
        assert data["id"]
        assert data["created_at"]
    finally:
        clear_mood_overrides(client)


def test_list_mood_entries_only_returns_current_users_entries(client, db: Session):
    user = create_user(db)
    other_user = create_user(db)

    MoodEntryService(db).create(user.id, "happy", 4, "Mine")
    MoodEntryService(db).create(other_user.id, "sad", 2, "Not mine")

    set_mood_overrides(client, db, user)

    try:
        response = client.get("/api/v1/moods")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["user_id"] == str(user.id)
        assert data[0]["mood"] == "happy"
    finally:
        clear_mood_overrides(client)


def test_list_mood_entries_supports_pagination(client, db: Session):
    user = create_user(db)
    service = MoodEntryService(db)
    service.create(user.id, "happy", 3)
    service.create(user.id, "calm", 2)
    service.create(user.id, "grateful", 5)

    set_mood_overrides(client, db, user)

    try:
        response = client.get("/api/v1/moods?limit=2&offset=1")

        assert response.status_code == 200
        assert len(response.json()) == 2
    finally:
        clear_mood_overrides(client)


def test_list_mood_entries_rejects_invalid_pagination(client, db: Session):
    user = create_user(db)
    set_mood_overrides(client, db, user)

    try:
        assert client.get("/api/v1/moods?limit=0").status_code == 422
        assert client.get("/api/v1/moods?limit=101").status_code == 422
        assert client.get("/api/v1/moods?offset=-1").status_code == 422
    finally:
        clear_mood_overrides(client)


def test_get_mood_entry(client, db: Session):
    user = create_user(db)
    entry = MoodEntryService(db).create(user.id, "calm", 3, "Relaxed")

    set_mood_overrides(client, db, user)

    try:
        response = client.get(f"/api/v1/moods/{entry.id}")

        assert response.status_code == 200
        assert response.json()["id"] == str(entry.id)
        assert response.json()["mood"] == "calm"
    finally:
        clear_mood_overrides(client)


def test_get_mood_entry_hides_other_users_entries(client, db: Session):
    user = create_user(db)
    other_user = create_user(db)
    entry = MoodEntryService(db).create(other_user.id, "sad", 2)

    set_mood_overrides(client, db, user)

    try:
        response = client.get(f"/api/v1/moods/{entry.id}")

        assert response.status_code == 404
    finally:
        clear_mood_overrides(client)


def test_get_mood_entry_returns_404_for_unknown_id(client, db: Session):
    user = create_user(db)
    set_mood_overrides(client, db, user)

    try:
        response = client.get(f"/api/v1/moods/{uuid4()}")

        assert response.status_code == 404
    finally:
        clear_mood_overrides(client)


def test_create_mood_entry_rejects_invalid_payload(client, db: Session):
    user = create_user(db)
    set_mood_overrides(client, db, user)

    try:
        invalid_mood = client.post(
            "/api/v1/moods",
            json={"mood": "unknown", "intensity": 3},
        )
        invalid_intensity = client.post(
            "/api/v1/moods",
            json={"mood": "happy", "intensity": 6},
        )
        oversized_note = client.post(
            "/api/v1/moods",
            json={
                "mood": "happy",
                "intensity": 3,
                "note": "x" * 501,
            },
        )

        assert invalid_mood.status_code == 422
        assert invalid_intensity.status_code == 422
        assert oversized_note.status_code == 422
    finally:
        clear_mood_overrides(client)


def test_delete_mood_entry(client, db: Session):
    user = create_user(db)
    entry = MoodEntryService(db).create(user.id, "excited", 5)

    set_mood_overrides(client, db, user)

    try:
        response = client.delete(f"/api/v1/moods/{entry.id}")

        assert response.status_code == 204
        assert response.content == b""

        follow_up = client.get(f"/api/v1/moods/{entry.id}")
        assert follow_up.status_code == 404
    finally:
        clear_mood_overrides(client)


def test_delete_mood_entry_hides_other_users_entries(client, db: Session):
    user = create_user(db)
    other_user = create_user(db)
    entry = MoodEntryService(db).create(other_user.id, "anxious", 4)

    set_mood_overrides(client, db, user)

    try:
        response = client.delete(f"/api/v1/moods/{entry.id}")

        assert response.status_code == 404
    finally:
        clear_mood_overrides(client)