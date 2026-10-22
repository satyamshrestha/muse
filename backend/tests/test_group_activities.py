from uuid import uuid4


def create_authenticated_user(client):
    email = f"{uuid4()}@example.com"
    password = "Password123!"

    signup = client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "password": password,
            "display_name": "Activity Tester",
        },
    )
    assert signup.status_code == 201

    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login.status_code == 200

    return {
        "Authorization": f"Bearer {login.json()['access_token']}"
    }


def create_group(client, headers, name="Activity Crew"):
    response = client.post(
        "/api/v1/groups",
        headers=headers,
        json={"name": name},
    )
    assert response.status_code == 201
    return response.json()


def create_activity(
    client,
    headers,
    group_id,
    title="Weekend plans",
    activity_type="poll",
):
    return client.post(
        f"/api/v1/groups/{group_id}/activities",
        headers=headers,
        json={
            "activity_type": activity_type,
            "title": title,
            "description": "Choose an activity",
        },
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


def test_create_group_activity(client):
    headers = create_authenticated_user(client)
    group = create_group(client, headers)

    response = create_activity(
        client, headers, group["id"]
    )

    assert response.status_code == 201
    data = response.json()
    assert data["group_id"] == group["id"]
    assert data["title"] == "Weekend plans"
    assert data["activity_type"] == "poll"
    assert data["description"] == "Choose an activity"
    assert data["created_by"]
    assert data["id"]
    assert data["created_at"]


def test_list_and_get_group_activities(client):
    headers = create_authenticated_user(client)
    group = create_group(client, headers)

    first = create_activity(
        client, headers, group["id"], "Movie night"
    )
    second = create_activity(
        client, headers, group["id"], "Study session", "event"
    )

    assert first.status_code == 201
    assert second.status_code == 201

    listing = client.get(
        f"/api/v1/groups/{group['id']}/activities",
        headers=headers,
    )
    assert listing.status_code == 200
    assert {item["id"] for item in listing.json()} == {
        first.json()["id"],
        second.json()["id"],
    }

    activity_id = first.json()["id"]
    detail = client.get(
        f"/api/v1/groups/{group['id']}/activities/{activity_id}",
        headers=headers,
    )
    assert detail.status_code == 200
    assert detail.json()["id"] == activity_id
    assert detail.json()["title"] == "Movie night"


def test_create_activity_requires_authentication(client):
    response = client.post(
        f"/api/v1/groups/{uuid4()}/activities",
        json={
            "activity_type": "poll",
            "title": "Weekend plans",
        },
    )
    assert response.status_code == 401


def test_create_activity_rejects_non_member(client):
    owner_headers = create_authenticated_user(client)
    outsider_headers = create_authenticated_user(client)
    group = create_group(client, owner_headers)

    response = create_activity(
        client, outsider_headers, group["id"]
    )

    assert response.status_code == 403


def test_list_activities_denies_non_member(client):
    owner_headers = create_authenticated_user(client)
    outsider_headers = create_authenticated_user(client)
    group = create_group(client, owner_headers)

    response = client.get(
        f"/api/v1/groups/{group['id']}/activities",
        headers=outsider_headers,
    )

    assert response.status_code == 403


def test_get_activity_rejects_unknown_activity(client):
    headers = create_authenticated_user(client)
    group = create_group(client, headers)

    response = client.get(
        f"/api/v1/groups/{group['id']}/activities/{uuid4()}",
        headers=headers,
    )

    assert response.status_code == 404


def test_get_activity_rejects_wrong_group_id(client):
    headers = create_authenticated_user(client)
    group = create_group(client, headers)
    other_group = create_group(client, headers, "Another Crew")

    activity = create_activity(client, headers, group["id"])
    assert activity.status_code == 201

    response = client.get(
        f"/api/v1/groups/{other_group['id']}/activities/"
        f"{activity.json()['id']}",
        headers=headers,
    )

    assert response.status_code == 404


def test_delete_activity_by_creator(client):
    headers = create_authenticated_user(client)
    group = create_group(client, headers)
    activity = create_activity(client, headers, group["id"])
    assert activity.status_code == 201

    response = client.delete(
        f"/api/v1/groups/{group['id']}/activities/"
        f"{activity.json()['id']}",
        headers=headers,
    )

    assert response.status_code == 204

    listing = client.get(
        f"/api/v1/groups/{group['id']}/activities",
        headers=headers,
    )
    assert listing.status_code == 200
    assert listing.json() == []


def test_delete_activity_rejects_non_creator(client):
    owner_headers = create_authenticated_user(client)
    member_headers = create_authenticated_user(client)
    group = create_group(client, owner_headers)

    add_group_member(
        client, owner_headers, member_headers, group["id"]
    )

    activity = create_activity(
        client, owner_headers, group["id"]
    )
    assert activity.status_code == 201

    response = client.delete(
        f"/api/v1/groups/{group['id']}/activities/"
        f"{activity.json()['id']}",
        headers=member_headers,
    )

    assert response.status_code == 403

    detail = client.get(
        f"/api/v1/groups/{group['id']}/activities/"
        f"{activity.json()['id']}",
        headers=member_headers,
    )
    assert detail.status_code == 200


def test_delete_activity_rejects_wrong_group_id(client):
    headers = create_authenticated_user(client)
    group = create_group(client, headers)
    other_group = create_group(client, headers, "Another Crew")

    activity = create_activity(client, headers, group["id"])
    assert activity.status_code == 201

    response = client.delete(
        f"/api/v1/groups/{other_group['id']}/activities/"
        f"{activity.json()['id']}",
        headers=headers,
    )

    assert response.status_code == 404


def test_list_activities_requires_authentication(client):
    response = client.get(
        f"/api/v1/groups/{uuid4()}/activities"
    )
    assert response.status_code == 401