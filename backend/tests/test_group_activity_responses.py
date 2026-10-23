from uuid import uuid4


def create_authenticated_user(client):
    email = f"{uuid4()}@example.com"
    password = "Password123!"

    signup = client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "password": password,
            "display_name": "Response Tester",
        },
    )
    assert signup.status_code == 201

    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login.status_code == 200

    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def create_group(client, headers, name="Response Crew"):
    result = client.post(
        "/api/v1/groups",
        headers=headers,
        json={"name": name},
    )
    assert result.status_code == 201
    return result.json()


def create_activity(client, headers, group_id):
    result = client.post(
        f"/api/v1/groups/{group_id}/activities",
        headers=headers,
        json={
            "activity_type": "poll",
            "title": "Weekend plans",
            "description": "Choose an activity",
        },
    )
    assert result.status_code == 201
    return result.json()


def create_response(client, headers, group_id, activity_id, answer="Movie night"):
    return client.post(
        f"/api/v1/groups/{group_id}/activities/{activity_id}/responses",
        headers=headers,
        json={"response": answer, "note": "Sounds good"},
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


def test_create_and_list_activity_responses(client):
    headers = create_authenticated_user(client)
    group = create_group(client, headers)
    activity = create_activity(client, headers, group["id"])

    created = create_response(
        client, headers, group["id"], activity["id"]
    )

    assert created.status_code == 201
    data = created.json()
    assert data["activity_id"] == activity["id"]
    assert data["response"] == "Movie night"
    assert data["note"] == "Sounds good"
    assert data["user_id"]
    assert data["created_at"]

    listing = client.get(
        f"/api/v1/groups/{group['id']}/activities/{activity['id']}/responses",
        headers=headers,
    )

    assert listing.status_code == 200
    assert len(listing.json()) == 1
    assert listing.json()[0]["id"] == data["id"]


def test_create_response_requires_authentication(client):
    headers = create_authenticated_user(client)
    group = create_group(client, headers)
    activity = create_activity(client, headers, group["id"])

    result = client.post(
        f"/api/v1/groups/{group['id']}/activities/{activity['id']}/responses",
        json={"response": "Movie night"},
    )

    assert result.status_code == 401


def test_create_response_rejects_non_member(client):
    owner_headers = create_authenticated_user(client)
    outsider_headers = create_authenticated_user(client)
    group = create_group(client, owner_headers)
    activity = create_activity(client, owner_headers, group["id"])

    result = create_response(
        client, outsider_headers, group["id"], activity["id"]
    )

    assert result.status_code == 403


def test_duplicate_response_returns_conflict(client):
    headers = create_authenticated_user(client)
    group = create_group(client, headers)
    activity = create_activity(client, headers, group["id"])

    first = create_response(
        client, headers, group["id"], activity["id"], "Movie night"
    )
    second = create_response(
        client, headers, group["id"], activity["id"], "Bowling"
    )

    assert first.status_code == 201
    assert second.status_code == 409


def test_get_response_by_id(client):
    headers = create_authenticated_user(client)
    group = create_group(client, headers)
    activity = create_activity(client, headers, group["id"])
    created = create_response(
        client, headers, group["id"], activity["id"]
    )
    assert created.status_code == 201

    result = client.get(
        f"/api/v1/groups/{group['id']}/activities/{activity['id']}"
        f"/responses/{created.json()['id']}",
        headers=headers,
    )

    assert result.status_code == 200
    assert result.json()["id"] == created.json()["id"]


def test_response_cannot_be_accessed_through_wrong_activity(client):
    headers = create_authenticated_user(client)
    group = create_group(client, headers)
    activity = create_activity(client, headers, group["id"])
    other_activity = create_activity(client, headers, group["id"])
    created = create_response(
        client, headers, group["id"], activity["id"]
    )
    assert created.status_code == 201

    result = client.get(
        f"/api/v1/groups/{group['id']}/activities/{other_activity['id']}"
        f"/responses/{created.json()['id']}",
        headers=headers,
    )

    assert result.status_code == 404


def test_delete_response_by_creator(client):
    headers = create_authenticated_user(client)
    group = create_group(client, headers)
    activity = create_activity(client, headers, group["id"])
    created = create_response(
        client, headers, group["id"], activity["id"]
    )
    assert created.status_code == 201

    response_id = created.json()["id"]
    deleted = client.delete(
        f"/api/v1/groups/{group['id']}/activities/{activity['id']}"
        f"/responses/{response_id}",
        headers=headers,
    )

    assert deleted.status_code == 204

    listing = client.get(
        f"/api/v1/groups/{group['id']}/activities/{activity['id']}/responses",
        headers=headers,
    )
    assert listing.status_code == 200
    assert listing.json() == []


def test_delete_response_rejects_non_creator(client):
    owner_headers = create_authenticated_user(client)
    member_headers = create_authenticated_user(client)
    group = create_group(client, owner_headers)
    activity = create_activity(client, owner_headers, group["id"])

    add_group_member(client, owner_headers, member_headers, group["id"])

    created = create_response(
        client, owner_headers, group["id"], activity["id"]
    )
    assert created.status_code == 201

    deleted = client.delete(
        f"/api/v1/groups/{group['id']}/activities/{activity['id']}"
        f"/responses/{created.json()['id']}",
        headers=member_headers,
    )

    assert deleted.status_code == 403


def test_wrong_group_id_returns_not_found(client):
    headers = create_authenticated_user(client)
    group = create_group(client, headers)
    other_group = create_group(client, headers, "Other Crew")
    activity = create_activity(client, headers, group["id"])

    result = create_response(
        client, headers, other_group["id"], activity["id"]
    )

    assert result.status_code == 404