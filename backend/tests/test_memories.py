from uuid import uuid4


def create_authenticated_user(client):
    email = f"{uuid4()}@example.com"
    password = "Password123!"

    signup = client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "password": password,
            "display_name": "Memory Tester",
        },
    )
    assert signup.status_code == 201

    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login.status_code == 200

    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def create_group(client, headers, name="Memory Crew"):
    result = client.post(
        "/api/v1/groups",
        headers=headers,
        json={"name": name},
    )
    assert result.status_code == 201
    return result.json()


def create_memory(
    client,
    headers,
    group_id,
    title="Summer trip",
    description="Our group trip.",
    memory_date=None,
):
    payload = {
        "title": title,
        "description": description,
    }
    if memory_date is not None:
        payload["memory_date"] = memory_date

    return client.post(
        f"/api/v1/groups/{group_id}/memories",
        headers=headers,
        json=payload,
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


def test_create_list_and_get_memory(client):
    headers = create_authenticated_user(client)
    group = create_group(client, headers)

    created = create_memory(client, headers, group["id"])

    assert created.status_code == 201, created.text
    data = created.json()
    assert data["group_id"] == group["id"]
    assert data["created_by"]
    assert data["title"] == "Summer trip"
    assert data["description"] == "Our group trip."
    assert data["created_at"]

    listing = client.get(
        f"/api/v1/groups/{group['id']}/memories",
        headers=headers,
    )
    assert listing.status_code == 200
    assert len(listing.json()) == 1

    detail = client.get(
        f"/api/v1/groups/{group['id']}/memories/{data['id']}",
        headers=headers,
    )
    assert detail.status_code == 200
    assert detail.json()["id"] == data["id"]


def test_create_memory_requires_authentication(client):
    headers = create_authenticated_user(client)
    group = create_group(client, headers)

    result = client.post(
        f"/api/v1/groups/{group['id']}/memories",
        json={"title": "Unauthenticated memory"},
    )

    assert result.status_code == 401


def test_non_member_cannot_read_or_create_memories(client):
    owner_headers = create_authenticated_user(client)
    outsider_headers = create_authenticated_user(client)
    group = create_group(client, owner_headers)

    created = create_memory(client, owner_headers, group["id"])
    assert created.status_code == 201, created.text

    listing = client.get(
        f"/api/v1/groups/{group['id']}/memories",
        headers=outsider_headers,
    )
    assert listing.status_code == 403

    attempt = create_memory(client, outsider_headers, group["id"])
    assert attempt.status_code == 403


def test_memory_cannot_be_accessed_through_wrong_group(client):
    headers = create_authenticated_user(client)
    group = create_group(client, headers)
    other_group = create_group(client, headers, "Another Memory Crew")

    created = create_memory(client, headers, group["id"])
    assert created.status_code == 201, created.text

    result = client.get(
        f"/api/v1/groups/{other_group['id']}/memories/"
        f"{created.json()['id']}",
        headers=headers,
    )

    assert result.status_code == 404


def test_update_memory_by_creator(client):
    headers = create_authenticated_user(client)
    group = create_group(client, headers)
    created = create_memory(client, headers, group["id"])
    assert created.status_code == 201, created.text

    result = client.put(
        f"/api/v1/groups/{group['id']}/memories/{created.json()['id']}",
        headers=headers,
        json={
            "title": "Updated trip",
            "description": "Updated details.",
            "memory_date": "2026-07-10T00:00:00Z",
        },
    )

    assert result.status_code == 200, result.text
    assert result.json()["title"] == "Updated trip"
    assert result.json()["description"] == "Updated details."
    assert result.json()["memory_date"] is not None


def test_member_cannot_update_another_members_memory(client):
    owner_headers = create_authenticated_user(client)
    member_headers = create_authenticated_user(client)
    group = create_group(client, owner_headers)
    add_group_member(client, owner_headers, member_headers, group["id"])

    created = create_memory(client, owner_headers, group["id"])
    assert created.status_code == 201, created.text

    result = client.put(
        f"/api/v1/groups/{group['id']}/memories/{created.json()['id']}",
        headers=member_headers,
        json={"title": "Hijacked", "description": "Changed."},
    )

    assert result.status_code == 403


def test_delete_memory_by_creator(client):
    headers = create_authenticated_user(client)
    group = create_group(client, headers)
    created = create_memory(client, headers, group["id"])
    assert created.status_code == 201, created.text

    memory_id = created.json()["id"]
    result = client.delete(
        f"/api/v1/groups/{group['id']}/memories/{memory_id}",
        headers=headers,
    )

    assert result.status_code == 204

    listing = client.get(
        f"/api/v1/groups/{group['id']}/memories",
        headers=headers,
    )
    assert listing.status_code == 200
    assert listing.json() == []


def test_member_cannot_delete_another_members_memory(client):
    owner_headers = create_authenticated_user(client)
    member_headers = create_authenticated_user(client)
    group = create_group(client, owner_headers)
    add_group_member(client, owner_headers, member_headers, group["id"])

    created = create_memory(client, owner_headers, group["id"])
    assert created.status_code == 201, created.text

    result = client.delete(
        f"/api/v1/groups/{group['id']}/memories/{created.json()['id']}",
        headers=member_headers,
    )

    assert result.status_code == 403


def test_list_memories_supports_pagination(client):
    headers = create_authenticated_user(client)
    group = create_group(client, headers)

    for index in range(3):
        created = create_memory(
            client,
            headers,
            group["id"],
            title=f"Memory {index}",
            description=f"Description {index}",
        )
        assert created.status_code == 201, created.text

    first_page = client.get(
        f"/api/v1/groups/{group['id']}/memories?limit=2&offset=0",
        headers=headers,
    )
    second_page = client.get(
        f"/api/v1/groups/{group['id']}/memories?limit=2&offset=2",
        headers=headers,
    )

    assert first_page.status_code == 200
    assert second_page.status_code == 200
    assert len(first_page.json()) == 2
    assert len(second_page.json()) == 1


def test_list_memories_rejects_invalid_pagination(client):
    headers = create_authenticated_user(client)
    group = create_group(client, headers)

    result = client.get(
        f"/api/v1/groups/{group['id']}/memories?limit=0",
        headers=headers,
    )

    assert result.status_code == 422


def test_memory_date_can_be_omitted(client):
    headers = create_authenticated_user(client)
    group = create_group(client, headers)

    created = create_memory(
        client,
        headers,
        group["id"],
        description=None,
    )

    assert created.status_code == 201, created.text
    assert created.json()["description"] is None
    assert created.json()["memory_date"] is None