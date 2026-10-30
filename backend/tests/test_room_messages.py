from uuid import uuid4

from app.models.user import User
from app.repositories.group_membership_repository import (
    GroupMembershipRepository,
)


def create_authenticated_user(client, db):
    email = f"{uuid4()}@example.com"
    password = "Password123!"

    signup = client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "password": password,
            "display_name": "Room Message Tester",
        },
    )
    assert signup.status_code == 201, signup.text

    login = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )
    assert login.status_code == 200, login.text

    user = db.query(User).filter(User.email == email).first()
    assert user is not None

    headers = {
        "Authorization": f"Bearer {login.json()['access_token']}"
    }

    return headers, user


def create_group(client, headers):
    response = client.post(
        "/api/v1/groups",
        headers=headers,
        json={"name": f"Room Message Test Group {uuid4()}"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_message(client, headers, group_id, content="Hello everyone!"):
    return client.post(
        f"/api/v1/groups/{group_id}/messages",
        headers=headers,
        json={"content": content},
    )


def test_create_list_and_delete_room_messages(client, db):
    headers, user = create_authenticated_user(client, db)
    group = create_group(client, headers)
    group_id = group["id"]

    first = create_message(client, headers, group_id, "First message")
    assert first.status_code == 201, first.text

    second = create_message(client, headers, group_id, "Second message")
    assert second.status_code == 201, second.text

    assert first.json()["user_id"] == str(user.id)
    assert first.json()["group_id"] == group_id

    listed = client.get(
        f"/api/v1/groups/{group_id}/messages",
        headers=headers,
    )

    assert listed.status_code == 200, listed.text
    assert [item["content"] for item in listed.json()] == [
        "First message",
        "Second message",
    ]

    message_id = first.json()["id"]

    deleted = client.delete(
        f"/api/v1/groups/{group_id}/messages/{message_id}",
        headers=headers,
    )

    assert deleted.status_code == 204

    listed_after_delete = client.get(
        f"/api/v1/groups/{group_id}/messages",
        headers=headers,
    )

    assert listed_after_delete.status_code == 200
    assert [item["content"] for item in listed_after_delete.json()] == [
        "Second message"
    ]


def test_room_message_endpoints_require_authentication(client, db):
    headers, _ = create_authenticated_user(client, db)
    group = create_group(client, headers)
    group_id = group["id"]

    response = client.get(
        f"/api/v1/groups/{group_id}/messages",
    )

    assert response.status_code == 401


def test_create_message_rejects_empty_content(client, db):
    headers, _ = create_authenticated_user(client, db)
    group = create_group(client, headers)

    response = create_message(
        client,
        headers,
        group["id"],
        "   ",
    )

    assert response.status_code == 422


def test_non_member_cannot_list_group_messages(client, db):
    owner_headers, _ = create_authenticated_user(client, db)
    group = create_group(client, owner_headers)

    outsider_headers, _ = create_authenticated_user(client, db)

    response = client.get(
        f"/api/v1/groups/{group['id']}/messages",
        headers=outsider_headers,
    )

    assert response.status_code == 403


def test_non_creator_cannot_delete_message(client, db):
    owner_headers, _ = create_authenticated_user(client, db)
    group = create_group(client, owner_headers)

    message = create_message(
        client,
        owner_headers,
        group["id"],
    )
    assert message.status_code == 201, message.text

    outsider_headers, outsider = create_authenticated_user(client, db)

    membership_repository = GroupMembershipRepository(db)
    membership_repository.create(
        user_id=outsider.id,
        group_id=group["id"],
    )
    db.commit()

    response = client.delete(
        f"/api/v1/groups/{group['id']}/messages/{message.json()['id']}",
        headers=outsider_headers,
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "Only the message creator can delete it"
    )


def test_non_member_cannot_create_message(client, db):
    owner_headers, _ = create_authenticated_user(client, db)
    group = create_group(client, owner_headers)

    outsider_headers, _ = create_authenticated_user(client, db)

    response = create_message(
        client,
        outsider_headers,
        group["id"],
    )

    assert response.status_code == 403


def test_wrong_group_message_path_returns_not_found(client, db):
    headers, _ = create_authenticated_user(client, db)
    group = create_group(client, headers)

    message = create_message(
        client,
        headers,
        group["id"],
    )
    assert message.status_code == 201, message.text

    wrong_group_id = str(uuid4())

    response = client.delete(
        f"/api/v1/groups/{wrong_group_id}/messages/{message.json()['id']}",
        headers=headers,
    )

    assert response.status_code == 404