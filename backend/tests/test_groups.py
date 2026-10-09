
from uuid import uuid4

from app.models.friend_group import FriendGroup
from app.models.group_membership import GroupMembership


def create_authenticated_user(client):
    email = f"{uuid4()}@example.com"
    password = "Password123!"

    signup = client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "password": password,
            "display_name": "Group Tester",
        },
    )
    assert signup.status_code == 201

    login = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )
    assert login.status_code == 200

    return {
        "Authorization": (
            f"Bearer {login.json()['access_token']}"
        )
    }


def test_create_group(client, db):
    headers = create_authenticated_user(client)

    response = client.post(
        "/api/v1/groups",
        headers=headers,
        json={"name": "MUSE Crew"},
    )

    assert response.status_code == 201

    data = response.json()
    assert data["name"] == "MUSE Crew"
    assert data["id"]

    # Verify the creator can retrieve the newly created group.
    group_response = client.get(
        f"/api/v1/groups/{data['id']}",
        headers=headers,
    )

    assert group_response.status_code == 200
    assert group_response.json()["id"] == data["id"]
    assert group_response.json()["name"] == "MUSE Crew"

    # Verify the group appears in the creator's group list.
    list_response = client.get(
        "/api/v1/groups",
        headers=headers,
    )

    assert list_response.status_code == 200
    assert any(
        group["id"] == data["id"]
        for group in list_response.json()
    )

def test_list_groups_returns_only_users_groups(client):
    headers = create_authenticated_user(client)

    created = client.post(
        "/api/v1/groups",
        headers=headers,
        json={"name": "My Group"},
    )
    assert created.status_code == 201

    response = client.get(
        "/api/v1/groups",
        headers=headers,
    )

    assert response.status_code == 200
    assert [group["name"] for group in response.json()] == [
        "My Group"
    ]


def test_get_group_for_member(client):
    headers = create_authenticated_user(client)

    created = client.post(
        "/api/v1/groups",
        headers=headers,
        json={"name": "MUSE Crew"},
    )
    group_id = created.json()["id"]

    response = client.get(
        f"/api/v1/groups/{group_id}",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["id"] == group_id
    assert response.json()["name"] == "MUSE Crew"


def test_get_group_denies_non_member(client):
    owner_headers = create_authenticated_user(client)
    other_headers = create_authenticated_user(client)

    created = client.post(
        "/api/v1/groups",
        headers=owner_headers,
        json={"name": "Private Group"},
    )
    group_id = created.json()["id"]

    response = client.get(
        f"/api/v1/groups/{group_id}",
        headers=other_headers,
    )

    assert response.status_code == 404


def test_list_groups_requires_authentication(client):
    response = client.get("/api/v1/groups")

    assert response.status_code == 401


def test_get_group_requires_authentication(client):
    response = client.get(
        f"/api/v1/groups/{uuid4()}"
    )

    assert response.status_code == 401