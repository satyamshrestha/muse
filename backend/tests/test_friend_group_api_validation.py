from uuid import uuid4


def create_authenticated_user(client):
    email = f"{uuid4()}@example.com"
    password = "Password123!"

    signup = client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "password": password,
            "display_name": "Group API Tester",
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


def test_create_group_rejects_empty_name(client):
    headers = create_authenticated_user(client)

    response = client.post(
        "/api/v1/groups",
        headers=headers,
        json={"name": ""},
    )

    assert response.status_code == 422


def test_create_group_rejects_name_longer_than_100_characters(client):
    headers = create_authenticated_user(client)

    response = client.post(
        "/api/v1/groups",
        headers=headers,
        json={"name": "G" * 101},
    )

    assert response.status_code == 422


def test_create_group_accepts_name_with_100_characters(client):
    headers = create_authenticated_user(client)
    name = "G" * 100

    response = client.post(
        "/api/v1/groups",
        headers=headers,
        json={"name": name},
    )

    assert response.status_code == 201
    assert response.json()["name"] == name


def test_get_group_rejects_invalid_uuid(client):
    headers = create_authenticated_user(client)

    response = client.get(
        "/api/v1/groups/not-a-uuid",
        headers=headers,
    )

    assert response.status_code == 422


def test_get_group_members_rejects_invalid_uuid(client):
    headers = create_authenticated_user(client)

    response = client.get(
        "/api/v1/groups/not-a-uuid/members",
        headers=headers,
    )

    assert response.status_code == 422


def test_leave_group_rejects_invalid_uuid(client):
    headers = create_authenticated_user(client)

    response = client.delete(
        "/api/v1/groups/not-a-uuid/leave",
        headers=headers,
    )

    assert response.status_code == 422