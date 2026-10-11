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
        "Authorization": f"Bearer {login.json()['access_token']}"
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

    group_response = client.get(
        f"/api/v1/groups/{data['id']}",
        headers=headers,
    )

    assert group_response.status_code == 200
    assert group_response.json()["id"] == data["id"]
    assert group_response.json()["name"] == "MUSE Crew"

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
    assert created.status_code == 201
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
    assert created.status_code == 201
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


def test_join_group_success(client):
    owner_headers = create_authenticated_user(client)
    member_headers = create_authenticated_user(client)

    created = client.post(
        "/api/v1/groups",
        headers=owner_headers,
        json={"name": "MUSE Crew"},
    )
    assert created.status_code == 201
    group_id = created.json()["id"]

    response = client.post(
        f"/api/v1/groups/{group_id}/join",
        headers=member_headers,
    )

    assert response.status_code == 200
    assert response.json()["id"] == group_id
    assert response.json()["name"] == "MUSE Crew"

    # Verify the new member can retrieve the group.
    group_response = client.get(
        f"/api/v1/groups/{group_id}",
        headers=member_headers,
    )
    assert group_response.status_code == 200

    # Verify the group appears in the new member's group list.
    list_response = client.get(
        "/api/v1/groups",
        headers=member_headers,
    )
    assert list_response.status_code == 200
    assert any(
        group["id"] == group_id
        for group in list_response.json()
    )


def test_join_group_rejects_unknown_group(client):
    headers = create_authenticated_user(client)

    response = client.post(
        f"/api/v1/groups/{uuid4()}/join",
        headers=headers,
    )

    assert response.status_code == 404


def test_join_group_rejects_duplicate_membership(client):
    headers = create_authenticated_user(client)

    created = client.post(
        "/api/v1/groups",
        headers=headers,
        json={"name": "MUSE Crew"},
    )
    assert created.status_code == 201
    group_id = created.json()["id"]

    response = client.post(
        f"/api/v1/groups/{group_id}/join",
        headers=headers,
    )

    assert response.status_code == 409


def test_join_group_requires_authentication(client):
    response = client.post(
        f"/api/v1/groups/{uuid4()}/join",
    )

    assert response.status_code == 401

def test_get_group_members_returns_members_for_group_member(client):
    owner_headers = create_authenticated_user(client)
    second_member_headers = create_authenticated_user(client)

    created = client.post(
        "/api/v1/groups",
        headers=owner_headers,
        json={"name": "MUSE Crew"},
    )
    assert created.status_code == 201
    group_id = created.json()["id"]

    joined = client.post(
        f"/api/v1/groups/{group_id}/join",
        headers=second_member_headers,
    )
    assert joined.status_code == 200

    response = client.get(
        f"/api/v1/groups/{group_id}/members",
        headers=owner_headers,
    )

    assert response.status_code == 200
    members = response.json()
    assert len(members) == 2
    assert len({member["id"] for member in members}) == 2
    assert {member["display_name"] for member in members} == {
        "Group Tester",
    }
    assert all("email" not in member for member in members)
    assert all("password_hash" not in member for member in members)


def test_get_group_members_denies_non_member(client):
    owner_headers = create_authenticated_user(client)
    other_headers = create_authenticated_user(client)

    created = client.post(
        "/api/v1/groups",
        headers=owner_headers,
        json={"name": "Private Group"},
    )
    assert created.status_code == 201
    group_id = created.json()["id"]

    response = client.get(
        f"/api/v1/groups/{group_id}/members",
        headers=other_headers,
    )

    assert response.status_code == 404


def test_get_group_members_rejects_unknown_group(client):
    headers = create_authenticated_user(client)

    response = client.get(
        f"/api/v1/groups/{uuid4()}/members",
        headers=headers,
    )

    assert response.status_code == 404


def test_get_group_members_requires_authentication(client):
    response = client.get(
        f"/api/v1/groups/{uuid4()}/members",
    )

    assert response.status_code == 401