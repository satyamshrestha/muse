from uuid import uuid4


def create_authenticated_user(client):
    email = f"{uuid4()}@example.com"
    password = "Password123!"

    signup = client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "password": password,
            "display_name": "Shared Note Tester",
        },
    )
    assert signup.status_code == 201

    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login.status_code == 200

    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def create_group(client, headers, name="Shared Note Crew"):
    result = client.post(
        "/api/v1/groups",
        headers=headers,
        json={"name": name},
    )
    assert result.status_code == 201
    return result.json()


def create_shared_note(
    client,
    headers,
    group_id,
    title="Project plan",
    content="Discuss the next feature.",
):
    return client.post(
        f"/api/v1/groups/{group_id}/shared-notes",
        headers=headers,
        json={"title": title, "content": content},
    )


def add_group_member(client, owner_headers, member_headers, group_id):
    invitation = client.post(
        f"/api/v1/groups/{group_id}/invitations",
        headers=owner_headers,
    )
    assert invitation.status_code == 201

    joined = client.post(
        "/api/v1/groups/join",
        headers=member_headers,
        json={"token": invitation.json()["token"]},
    )
    assert joined.status_code == 200


def test_create_list_and_get_shared_note(client):
    headers = create_authenticated_user(client)
    group = create_group(client, headers)

    created = create_shared_note(client, headers, group["id"])

    assert created.status_code == 201
    data = created.json()
    assert data["group_id"] == group["id"]
    assert data["created_by"]
    assert data["title"] == "Project plan"
    assert data["content"] == "Discuss the next feature."
    assert data["created_at"]
    assert data["updated_at"]

    listing = client.get(
        f"/api/v1/groups/{group['id']}/shared-notes",
        headers=headers,
    )
    assert listing.status_code == 200
    assert len(listing.json()) == 1

    detail = client.get(
        f"/api/v1/groups/{group['id']}/shared-notes/{data['id']}",
        headers=headers,
    )
    assert detail.status_code == 200
    assert detail.json()["id"] == data["id"]


def test_create_shared_note_requires_authentication(client):
    headers = create_authenticated_user(client)
    group = create_group(client, headers)

    result = client.post(
        f"/api/v1/groups/{group['id']}/shared-notes",
        json={"title": "Unauthenticated", "content": "Not allowed"},
    )

    assert result.status_code == 401


def test_non_member_cannot_read_or_create_shared_notes(client):
    owner_headers = create_authenticated_user(client)
    outsider_headers = create_authenticated_user(client)
    group = create_group(client, owner_headers)

    created = create_shared_note(client, owner_headers, group["id"])
    assert created.status_code == 201

    listing = client.get(
        f"/api/v1/groups/{group['id']}/shared-notes",
        headers=outsider_headers,
    )
    assert listing.status_code == 403

    attempt = create_shared_note(client, outsider_headers, group["id"])
    assert attempt.status_code == 403


def test_shared_note_cannot_be_accessed_through_wrong_group(client):
    headers = create_authenticated_user(client)
    group = create_group(client, headers)
    other_group = create_group(client, headers, "Another Crew")

    created = create_shared_note(client, headers, group["id"])
    assert created.status_code == 201

    result = client.get(
        f"/api/v1/groups/{other_group['id']}/shared-notes/"
        f"{created.json()['id']}",
        headers=headers,
    )

    assert result.status_code == 404


def test_update_shared_note_by_creator(client):
    headers = create_authenticated_user(client)
    group = create_group(client, headers)
    created = create_shared_note(client, headers, group["id"])
    assert created.status_code == 201

    result = client.put(
        f"/api/v1/groups/{group['id']}/shared-notes/{created.json()['id']}",
        headers=headers,
        json={"title": "Updated plan", "content": "Updated content."},
    )

    assert result.status_code == 200
    assert result.json()["title"] == "Updated plan"
    assert result.json()["content"] == "Updated content."


def test_member_cannot_update_another_members_note(client):
    owner_headers = create_authenticated_user(client)
    member_headers = create_authenticated_user(client)
    group = create_group(client, owner_headers)
    add_group_member(client, owner_headers, member_headers, group["id"])

    created = create_shared_note(client, owner_headers, group["id"])
    assert created.status_code == 201

    result = client.put(
        f"/api/v1/groups/{group['id']}/shared-notes/{created.json()['id']}",
        headers=member_headers,
        json={"title": "Hijacked", "content": "Changed content."},
    )

    assert result.status_code == 403


def test_delete_shared_note_by_creator(client):
    headers = create_authenticated_user(client)
    group = create_group(client, headers)
    created = create_shared_note(client, headers, group["id"])
    assert created.status_code == 201

    note_id = created.json()["id"]
    result = client.delete(
        f"/api/v1/groups/{group['id']}/shared-notes/{note_id}",
        headers=headers,
    )

    assert result.status_code == 204

    listing = client.get(
        f"/api/v1/groups/{group['id']}/shared-notes",
        headers=headers,
    )
    assert listing.status_code == 200
    assert listing.json() == []


def test_member_cannot_delete_another_members_note(client):
    owner_headers = create_authenticated_user(client)
    member_headers = create_authenticated_user(client)
    group = create_group(client, owner_headers)
    add_group_member(client, owner_headers, member_headers, group["id"])

    created = create_shared_note(client, owner_headers, group["id"])
    assert created.status_code == 201

    result = client.delete(
        f"/api/v1/groups/{group['id']}/shared-notes/{created.json()['id']}",
        headers=member_headers,
    )

    assert result.status_code == 403


def test_list_shared_notes_supports_pagination(client):
    headers = create_authenticated_user(client)
    group = create_group(client, headers)

    for index in range(3):
        created = create_shared_note(
            client,
            headers,
            group["id"],
            title=f"Note {index}",
            content=f"Content {index}",
        )
        assert created.status_code == 201

    first_page = client.get(
        f"/api/v1/groups/{group['id']}/shared-notes?limit=2&offset=0",
        headers=headers,
    )
    second_page = client.get(
        f"/api/v1/groups/{group['id']}/shared-notes?limit=2&offset=2",
        headers=headers,
    )

    assert first_page.status_code == 200
    assert second_page.status_code == 200
    assert len(first_page.json()) == 2
    assert len(second_page.json()) == 1


def test_list_shared_notes_rejects_invalid_pagination(client):
    headers = create_authenticated_user(client)
    group = create_group(client, headers)

    result = client.get(
        f"/api/v1/groups/{group['id']}/shared-notes?limit=0",
        headers=headers,
    )

    assert result.status_code == 422