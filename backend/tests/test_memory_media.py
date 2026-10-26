from uuid import uuid4

from app.models.media import Media
from app.models.user import User


def create_authenticated_user(client, db):
    email = f"{uuid4()}@example.com"
    password = "Password123!"

    signup = client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "password": password,
            "display_name": "Memory Media Tester",
        },
    )
    assert signup.status_code == 201, signup.text

    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login.status_code == 200, login.text

    user = db.query(User).filter(User.email == email).first()
    assert user is not None

    headers = {
        "Authorization": f"Bearer {login.json()['access_token']}"
    }
    return headers, user


def create_group(client, headers, name="Memory Media Crew"):
    result = client.post(
        "/api/v1/groups",
        headers=headers,
        json={"name": name},
    )
    assert result.status_code == 201, result.text
    return result.json()


def create_memory(client, headers, group_id, title="Test Memory"):
    result = client.post(
        f"/api/v1/groups/{group_id}/memories",
        headers=headers,
        json={
            "title": title,
            "description": "Memory media integration test",
        },
    )
    assert result.status_code == 201, result.text
    return result.json()


def create_media(db, user):
    media = Media(
        uploaded_by=user.id,
        object_key=f"integration-tests/{uuid4()}.jpg",
        media_type="image",
        mime_type="image/jpeg",
    )
    db.add(media)
    db.flush()
    db.commit()
    return media


def add_group_member(client, owner_headers, member_headers, group_id):
    invitation = client.post(
        f"/api/v1/groups/{group_id}/invitations",
        headers=owner_headers,
    )
    assert invitation.status_code == 201, invitation.text

    joined = client.post(
        "/api/v1/groups/join",
        headers=member_headers,
        json={"token": invitation.json()["token"]},
    )
    assert joined.status_code == 200, joined.text


def test_attach_and_list_memory_media(client, db):
    headers, user = create_authenticated_user(client, db)
    group = create_group(client, headers)
    memory = create_memory(client, headers, group["id"])
    media = create_media(db, user)

    attached = client.post(
        f"/api/v1/groups/{group['id']}/memories/{memory['id']}/media",
        headers=headers,
        json={"media_id": str(media.id)},
    )

    assert attached.status_code == 201, attached.text
    link = attached.json()
    assert link["memory_id"] == memory["id"]
    assert link["media_id"] == str(media.id)
    assert link["id"]
    assert link["created_at"]

    listing = client.get(
        f"/api/v1/groups/{group['id']}/memories/{memory['id']}/media",
        headers=headers,
    )

    assert listing.status_code == 200, listing.text
    assert len(listing.json()) == 1
    assert listing.json()[0]["id"] == link["id"]


def test_attach_memory_media_requires_authentication(client, db):
    headers, user = create_authenticated_user(client, db)
    group = create_group(client, headers)
    memory = create_memory(client, headers, group["id"])
    media = create_media(db, user)

    result = client.post(
        f"/api/v1/groups/{group['id']}/memories/{memory['id']}/media",
        json={"media_id": str(media.id)},
    )

    assert result.status_code == 401


def test_non_member_cannot_attach_or_list_memory_media(client, db):
    owner_headers, owner = create_authenticated_user(client, db)
    outsider_headers, outsider = create_authenticated_user(client, db)
    group = create_group(client, owner_headers)
    memory = create_memory(client, owner_headers, group["id"])
    media = create_media(db, outsider)

    attach = client.post(
        f"/api/v1/groups/{group['id']}/memories/{memory['id']}/media",
        headers=outsider_headers,
        json={"media_id": str(media.id)},
    )
    listing = client.get(
        f"/api/v1/groups/{group['id']}/memories/{memory['id']}/media",
        headers=outsider_headers,
    )

    assert attach.status_code == 403
    assert listing.status_code == 403


def test_cannot_attach_another_users_media(client, db):
    owner_headers, owner = create_authenticated_user(client, db)
    member_headers, member = create_authenticated_user(client, db)
    group = create_group(client, owner_headers)
    add_group_member(client, owner_headers, member_headers, group["id"])
    memory = create_memory(client, owner_headers, group["id"])
    media = create_media(db, member)

    result = client.post(
        f"/api/v1/groups/{group['id']}/memories/{memory['id']}/media",
        headers=owner_headers,
        json={"media_id": str(media.id)},
    )

    assert result.status_code == 403


def test_duplicate_attachment_returns_conflict(client, db):
    headers, user = create_authenticated_user(client, db)
    group = create_group(client, headers)
    memory = create_memory(client, headers, group["id"])
    media = create_media(db, user)
    url = (
        f"/api/v1/groups/{group['id']}/memories/"
        f"{memory['id']}/media"
    )

    first = client.post(
        url,
        headers=headers,
        json={"media_id": str(media.id)},
    )
    second = client.post(
        url,
        headers=headers,
        json={"media_id": str(media.id)},
    )

    assert first.status_code == 201, first.text
    assert second.status_code == 409


def test_detach_memory_media_by_memory_creator(client, db):
    headers, user = create_authenticated_user(client, db)
    group = create_group(client, headers)
    memory = create_memory(client, headers, group["id"])
    media = create_media(db, user)

    attached = client.post(
        f"/api/v1/groups/{group['id']}/memories/{memory['id']}/media",
        headers=headers,
        json={"media_id": str(media.id)},
    )
    assert attached.status_code == 201, attached.text

    link_id = attached.json()["id"]
    result = client.delete(
        f"/api/v1/groups/{group['id']}/memories/"
        f"{memory['id']}/media/{link_id}",
        headers=headers,
    )

    assert result.status_code == 204

    listing = client.get(
        f"/api/v1/groups/{group['id']}/memories/{memory['id']}/media",
        headers=headers,
    )
    assert listing.status_code == 200
    assert listing.json() == []

    # Detaching the link must not delete the underlying media record.
    assert db.get(Media, media.id) is not None


def test_group_member_cannot_detach_media_from_another_members_memory(
    client,
    db,
):
    owner_headers, owner = create_authenticated_user(client, db)
    member_headers, member = create_authenticated_user(client, db)
    group = create_group(client, owner_headers)
    add_group_member(client, owner_headers, member_headers, group["id"])
    memory = create_memory(client, owner_headers, group["id"])
    media = create_media(db, owner)

    attached = client.post(
        f"/api/v1/groups/{group['id']}/memories/{memory['id']}/media",
        headers=owner_headers,
        json={"media_id": str(media.id)},
    )
    assert attached.status_code == 201, attached.text

    result = client.delete(
        f"/api/v1/groups/{group['id']}/memories/"
        f"{memory['id']}/media/{attached.json()['id']}",
        headers=member_headers,
    )

    assert result.status_code == 403


def test_attach_media_to_wrong_group_memory_returns_not_found(client, db):
    headers, user = create_authenticated_user(client, db)
    group = create_group(client, headers, "First Group")
    other_group = create_group(client, headers, "Second Group")
    memory = create_memory(client, headers, other_group["id"])
    media = create_media(db, user)

    result = client.post(
        f"/api/v1/groups/{group['id']}/memories/{memory['id']}/media",
        headers=headers,
        json={"media_id": str(media.id)},
    )

    assert result.status_code == 404


def test_list_memory_media_rejects_invalid_pagination(client, db):
    headers, user = create_authenticated_user(client, db)
    group = create_group(client, headers)
    memory = create_memory(client, headers, group["id"])

    result = client.get(
        f"/api/v1/groups/{group['id']}/memories/{memory['id']}/media"
        "?limit=0",
        headers=headers,
    )

    assert result.status_code == 422