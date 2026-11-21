from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.auth.jwt import get_current_user_id
from app.models.user import User
from app.services.dependencies import get_mood_entry_service
from app.services.mood_entry_service import MoodEntryService


def create_user(db: Session) -> User:
    user = User(
        email=f"{uuid4().hex}@example.com",
        password_hash="test-hash",
        display_name="Mood API Validation Test",
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


def test_create_mood_entry_rejects_empty_mood(client, db: Session):
    user = create_user(db)
    set_mood_overrides(client, db, user)

    try:
        response = client.post(
            "/api/v1/moods",
            json={"mood": "", "intensity": 3},
        )

        assert response.status_code == 422
    finally:
        clear_mood_overrides(client)


@pytest.mark.parametrize("intensity", [0, 6])
def test_create_mood_entry_rejects_intensity_out_of_schema_range(
    client,
    db: Session,
    intensity,
):
    user = create_user(db)
    set_mood_overrides(client, db, user)

    try:
        response = client.post(
            "/api/v1/moods",
            json={"mood": "happy", "intensity": intensity},
        )

        assert response.status_code == 422
    finally:
        clear_mood_overrides(client)


def test_create_mood_entry_rejects_missing_required_fields(
    client,
    db: Session,
):
    user = create_user(db)
    set_mood_overrides(client, db, user)

    try:
        response = client.post(
            "/api/v1/moods",
            json={"note": "Missing mood and intensity"},
        )

        assert response.status_code == 422
    finally:
        clear_mood_overrides(client)


def test_create_mood_entry_rejects_note_over_500_characters(
    client,
    db: Session,
):
    user = create_user(db)
    set_mood_overrides(client, db, user)

    try:
        response = client.post(
            "/api/v1/moods",
            json={
                "mood": "happy",
                "intensity": 3,
                "note": "x" * 501,
            },
        )

        assert response.status_code == 422
    finally:
        clear_mood_overrides(client)


def test_create_mood_entry_accepts_note_of_500_characters(
    client,
    db: Session,
):
    user = create_user(db)
    set_mood_overrides(client, db, user)

    note = "x" * 500

    try:
        response = client.post(
            "/api/v1/moods",
            json={
                "mood": "happy",
                "intensity": 3,
                "note": note,
            },
        )

        assert response.status_code == 201
        assert response.json()["note"] == note
    finally:
        clear_mood_overrides(client)


def test_get_mood_entry_rejects_invalid_uuid(client, db: Session):
    user = create_user(db)
    set_mood_overrides(client, db, user)

    try:
        response = client.get("/api/v1/moods/not-a-uuid")

        assert response.status_code == 422
    finally:
        clear_mood_overrides(client)


def test_delete_mood_entry_rejects_invalid_uuid(client, db: Session):
    user = create_user(db)
    set_mood_overrides(client, db, user)

    try:
        response = client.delete("/api/v1/moods/not-a-uuid")

        assert response.status_code == 422
    finally:
        clear_mood_overrides(client)


def test_list_mood_entries_requires_authentication(client):
    response = client.get("/api/v1/moods")

    assert response.status_code in (401, 403)