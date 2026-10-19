from uuid import uuid4

from sqlalchemy.orm import Session

from app.auth.jwt import get_current_user_id
from app.models.user import User
from app.services.dependencies import get_personal_note_service
from app.services.personal_note_service import PersonalNoteService


def create_user(db: Session) -> User:
    user = User(
        email=f"{uuid4().hex}@example.com",
        password_hash="test-hash",
        display_name="Personal Note API Test User",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def set_note_overrides(client, db: Session, user: User) -> None:
    client.app.dependency_overrides[get_current_user_id] = lambda: user.id
    client.app.dependency_overrides[get_personal_note_service] = (
        lambda: PersonalNoteService(db)
    )


def clear_note_overrides(client) -> None:
    client.app.dependency_overrides.pop(get_current_user_id, None)
    client.app.dependency_overrides.pop(get_personal_note_service, None)


def test_create_personal_note(client, db: Session):
    user = create_user(db)
    set_note_overrides(client, db, user)

    try:
        response = client.post(
            "/api/v1/notes",
            json={"title": "  My ideas  ", "content": "  Build something useful.  "},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] == str(user.id)
        assert data["title"] == "My ideas"
        assert data["content"] == "Build something useful."
        assert data["id"]
        assert data["created_at"]
        assert data["updated_at"]
    finally:
        clear_note_overrides(client)


def test_list_personal_notes_only_returns_current_users_notes(client, db: Session):
    user = create_user(db)
    other_user = create_user(db)

    PersonalNoteService(db).create(user.id, "Mine", "My content")
    PersonalNoteService(db).create(other_user.id, "Theirs", "Their content")

    set_note_overrides(client, db, user)

    try:
        response = client.get("/api/v1/notes")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["user_id"] == str(user.id)
        assert data[0]["title"] == "Mine"
    finally:
        clear_note_overrides(client)


def test_list_personal_notes_supports_pagination(client, db: Session):
    user = create_user(db)
    service = PersonalNoteService(db)

    service.create(user.id, "One", "First")
    service.create(user.id, "Two", "Second")
    service.create(user.id, "Three", "Third")

    set_note_overrides(client, db, user)

    try:
        response = client.get("/api/v1/notes?limit=2&offset=1")

        assert response.status_code == 200
        assert len(response.json()) == 2
    finally:
        clear_note_overrides(client)


def test_list_personal_notes_rejects_invalid_pagination(client, db: Session):
    user = create_user(db)
    set_note_overrides(client, db, user)

    try:
        assert client.get("/api/v1/notes?limit=0").status_code == 422
        assert client.get("/api/v1/notes?limit=101").status_code == 422
        assert client.get("/api/v1/notes?offset=-1").status_code == 422
    finally:
        clear_note_overrides(client)


def test_get_personal_note(client, db: Session):
    user = create_user(db)
    note = PersonalNoteService(db).create(user.id, "My note", "My content")
    set_note_overrides(client, db, user)

    try:
        response = client.get(f"/api/v1/notes/{note.id}")

        assert response.status_code == 200
        assert response.json()["id"] == str(note.id)
        assert response.json()["title"] == "My note"
    finally:
        clear_note_overrides(client)


def test_get_personal_note_hides_another_users_note(client, db: Session):
    user = create_user(db)
    other_user = create_user(db)
    note = PersonalNoteService(db).create(other_user.id, "Private", "Secret")
    set_note_overrides(client, db, user)

    try:
        response = client.get(f"/api/v1/notes/{note.id}")

        assert response.status_code == 404
    finally:
        clear_note_overrides(client)


def test_get_personal_note_returns_404_for_unknown_id(client, db: Session):
    user = create_user(db)
    set_note_overrides(client, db, user)

    try:
        response = client.get(f"/api/v1/notes/{uuid4()}")

        assert response.status_code == 404
    finally:
        clear_note_overrides(client)


def test_update_personal_note(client, db: Session):
    user = create_user(db)
    note = PersonalNoteService(db).create(user.id, "Old title", "Old content")
    set_note_overrides(client, db, user)

    try:
        response = client.put(
            f"/api/v1/notes/{note.id}",
            json={"title": "Updated title", "content": "Updated content"},
        )

        assert response.status_code == 200
        assert response.json()["title"] == "Updated title"
        assert response.json()["content"] == "Updated content"
    finally:
        clear_note_overrides(client)


def test_update_personal_note_hides_another_users_note(client, db: Session):
    user = create_user(db)
    other_user = create_user(db)
    note = PersonalNoteService(db).create(other_user.id, "Private", "Secret")
    set_note_overrides(client, db, user)

    try:
        response = client.put(
            f"/api/v1/notes/{note.id}",
            json={"title": "Hijacked", "content": "Changed"},
        )

        assert response.status_code == 404
        assert PersonalNoteService(db).get_for_user(other_user.id, note.id).title == "Private"
    finally:
        clear_note_overrides(client)


def test_update_personal_note_rejects_invalid_payload(client, db: Session):
    user = create_user(db)
    note = PersonalNoteService(db).create(user.id, "Original", "Original content")
    set_note_overrides(client, db, user)

    try:
        response = client.put(
            f"/api/v1/notes/{note.id}",
            json={"title": "   ", "content": "Updated content"},
        )

        assert response.status_code == 422
    finally:
        clear_note_overrides(client)


def test_delete_personal_note(client, db: Session):
    user = create_user(db)
    note = PersonalNoteService(db).create(user.id, "Temporary", "Delete me")
    set_note_overrides(client, db, user)

    try:
        response = client.delete(f"/api/v1/notes/{note.id}")

        assert response.status_code == 204
        assert response.content == b""

        follow_up = client.get(f"/api/v1/notes/{note.id}")
        assert follow_up.status_code == 404
    finally:
        clear_note_overrides(client)


def test_delete_personal_note_hides_another_users_note(client, db: Session):
    user = create_user(db)
    other_user = create_user(db)
    note = PersonalNoteService(db).create(other_user.id, "Private", "Secret")
    set_note_overrides(client, db, user)

    try:
        response = client.delete(f"/api/v1/notes/{note.id}")

        assert response.status_code == 404
        assert PersonalNoteService(db).get_for_user(other_user.id, note.id).id == note.id
    finally:
        clear_note_overrides(client)


def test_create_personal_note_rejects_invalid_payload(client, db: Session):
    user = create_user(db)
    set_note_overrides(client, db, user)

    try:
        empty_title = client.post(
            "/api/v1/notes",
            json={"title": "   ", "content": "Some content"},
        )
        missing_content = client.post(
            "/api/v1/notes",
            json={"title": "A title"},
        )

        assert empty_title.status_code == 422
        assert missing_content.status_code == 422
    finally:
        clear_note_overrides(client)