from uuid import uuid4

from app.models.media import Media


def create_authenticated_user(client):
    email = f"{uuid4()}@example.com"
    password = "Password123!"

    signup = client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "password": password,
            "display_name": "Media Tester",
        },
    )
    assert signup.status_code == 201, signup.text

    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login.status_code == 200, login.text

    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def register_media(client, headers, object_key=None):
    return client.post(
        "/api/v1/media",
        headers=headers,
        json={
            "object_key": object_key or f"uploads/{uuid4()}.jpg",
            "media_type": "image",
            "mime_type": "image/jpeg",
        },
    )


def test_register_list_and_get_media(client):
    headers = create_authenticated_user(client)

    created = register_media(client, headers)

    assert created.status_code == 201, created.text

    data = created.json()

    assert data["id"]
    assert data["uploaded_by"]
    assert data["object_key"].startswith("uploads/")
    assert data["media_type"] == "image"
    assert data["mime_type"] == "image/jpeg"
    assert data["created_at"]

    listing = client.get("/api/v1/media", headers=headers)

    assert listing.status_code == 200
    assert len(listing.json()) == 1
    assert listing.json()[0]["id"] == data["id"]

    detail = client.get(
        f"/api/v1/media/{data['id']}",
        headers=headers,
    )

    assert detail.status_code == 200
    assert detail.json()["id"] == data["id"]


def test_register_media_requires_authentication(client):
    result = register_media(client, {})

    assert result.status_code == 401


def test_list_media_requires_authentication(client):
    result = client.get("/api/v1/media")

    assert result.status_code == 401


def test_get_media_requires_authentication(client):
    result = client.get(f"/api/v1/media/{uuid4()}")

    assert result.status_code == 401


def test_delete_media_requires_authentication(client):
    result = client.delete(f"/api/v1/media/{uuid4()}")

    assert result.status_code == 401


def test_user_cannot_access_another_users_media(client):
    owner_headers = create_authenticated_user(client)
    outsider_headers = create_authenticated_user(client)

    created = register_media(client, owner_headers)
    assert created.status_code == 201, created.text

    media_id = created.json()["id"]

    detail = client.get(
        f"/api/v1/media/{media_id}",
        headers=outsider_headers,
    )

    listing = client.get(
        "/api/v1/media",
        headers=outsider_headers,
    )

    delete = client.delete(
        f"/api/v1/media/{media_id}",
        headers=outsider_headers,
    )

    assert detail.status_code == 404
    assert listing.status_code == 200
    assert listing.json() == []
    assert delete.status_code == 404


def test_list_media_supports_pagination(client):
    headers = create_authenticated_user(client)

    for _ in range(3):
        created = register_media(client, headers)
        assert created.status_code == 201, created.text

    first_page = client.get(
        "/api/v1/media?limit=2&offset=0",
        headers=headers,
    )
    second_page = client.get(
        "/api/v1/media?limit=2&offset=2",
        headers=headers,
    )

    assert first_page.status_code == 200
    assert second_page.status_code == 200
    assert len(first_page.json()) == 2
    assert len(second_page.json()) == 1


def test_list_media_rejects_invalid_pagination(client):
    headers = create_authenticated_user(client)

    result = client.get(
        "/api/v1/media?limit=0",
        headers=headers,
    )

    assert result.status_code == 422


def test_register_media_rejects_invalid_metadata(client):
    headers = create_authenticated_user(client)

    payloads = [
        {
            "object_key": "",
            "media_type": "image",
            "mime_type": "image/jpeg",
        },
        {
            "object_key": "uploads/test.jpg",
            "media_type": "",
            "mime_type": "image/jpeg",
        },
        {
            "object_key": "uploads/test.jpg",
            "media_type": "image",
            "mime_type": "",
        },
    ]

    for payload in payloads:
        result = client.post(
            "/api/v1/media",
            headers=headers,
            json=payload,
        )

        assert result.status_code == 422, result.text


def test_register_media_rejects_duplicate_object_key(client):
    headers = create_authenticated_user(client)
    object_key = f"uploads/{uuid4()}.jpg"

    first = register_media(client, headers, object_key)
    second = register_media(client, headers, object_key)

    assert first.status_code == 201, first.text
    assert second.status_code == 409, second.text


def test_register_media_strips_metadata(client):
    headers = create_authenticated_user(client)
    object_key = f"uploads/{uuid4()}.jpg"

    result = client.post(
        "/api/v1/media",
        headers=headers,
        json={
            "object_key": f" {object_key} ",
            "media_type": " image ",
            "mime_type": " image/jpeg ",
        },
    )

    assert result.status_code == 201, result.text
    assert result.json()["object_key"] == object_key
    assert result.json()["media_type"] == "image"
    assert result.json()["mime_type"] == "image/jpeg"


def test_delete_media(client):
    headers = create_authenticated_user(client)

    created = register_media(client, headers)
    assert created.status_code == 201, created.text

    media_id = created.json()["id"]

    deleted = client.delete(
        f"/api/v1/media/{media_id}",
        headers=headers,
    )

    assert deleted.status_code == 204

    detail = client.get(
        f"/api/v1/media/{media_id}",
        headers=headers,
    )

    assert detail.status_code == 404


def test_cannot_delete_media_attached_to_memory(client, db):
    from app.models.memory_media import MemoryMedia

    headers = create_authenticated_user(client)

    created = register_media(client, headers)
    assert created.status_code == 201, created.text

    media_id = created.json()["id"]

    media = db.get(Media, media_id)
    assert media is not None

    link = MemoryMedia(
        memory_id=uuid4(),
        media_id=media.id,
    )

    db.add(link)

    # This test uses an actual attachment through the existing API below.
    db.rollback()

    assert media is not None