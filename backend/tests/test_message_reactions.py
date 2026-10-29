from uuid import uuid4

from app.models.room_message import RoomMessage
from app.models.user import User


def create_authenticated_user(client, db):
    email = f"{uuid4()}@example.com"
    password = "Password123!"

    signup = client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "password": password,
            "display_name": "Reaction Tester",
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

    return {
        "Authorization": f"Bearer {login.json()['access_token']}"
    }, user


def create_group(client, headers):
    response = client.post(
        "/api/v1/groups",
        headers=headers,
        json={"name": f"Reaction Test Group {uuid4()}"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_message(db, group_id, user_id):
    message = RoomMessage(
        group_id=group_id,
        user_id=user_id,
        content="Message reaction API test",
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def test_create_list_update_and_delete_reaction(client, db):
    headers, user = create_authenticated_user(client, db)
    group = create_group(client, headers)
    message = create_message(db, group["id"], user.id)

    base = (
        f"/api/v1/groups/{group['id']}/messages/"
        f"{message.id}/reactions"
    )

    created = client.post(
        base,
        headers=headers,
        json={"reaction": "👍"},
    )
    assert created.status_code == 201, created.text
    assert created.json()["reaction"] == "👍"
    reaction_id = created.json()["id"]

    listing = client.get(base, headers=headers)
    assert listing.status_code == 200, listing.text
    assert len(listing.json()) == 1
    assert listing.json()[0]["id"] == reaction_id

    updated = client.put(
        f"{base}/{reaction_id}",
        headers=headers,
        json={"reaction": "🎉"},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["reaction"] == "🎉"

    deleted = client.delete(
        f"{base}/{reaction_id}",
        headers=headers,
    )
    assert deleted.status_code == 204

    listing_after_delete = client.get(base, headers=headers)
    assert listing_after_delete.status_code == 200
    assert listing_after_delete.json() == []


def test_reaction_endpoints_require_authentication(client, db):
    headers, user = create_authenticated_user(client, db)
    group = create_group(client, headers)
    message = create_message(db, group["id"], user.id)

    base = (
        f"/api/v1/groups/{group['id']}/messages/"
        f"{message.id}/reactions"
    )

    response = client.get(base)

    assert response.status_code == 401


def test_duplicate_reaction_returns_conflict(client, db):
    headers, user = create_authenticated_user(client, db)
    group = create_group(client, headers)
    message = create_message(db, group["id"], user.id)

    base = (
        f"/api/v1/groups/{group['id']}/messages/"
        f"{message.id}/reactions"
    )

    first = client.post(
        base,
        headers=headers,
        json={"reaction": "👍"},
    )
    assert first.status_code == 201, first.text

    second = client.post(
        base,
        headers=headers,
        json={"reaction": "😂"},
    )
    assert second.status_code == 409, second.text


def test_empty_reaction_returns_validation_error(client, db):
    headers, user = create_authenticated_user(client, db)
    group = create_group(client, headers)
    message = create_message(db, group["id"], user.id)

    response = client.post(
        f"/api/v1/groups/{group['id']}/messages/"
        f"{message.id}/reactions",
        headers=headers,
        json={"reaction": "   "},
    )

    assert response.status_code == 422


def test_non_member_cannot_list_reactions(client, db):
    owner_headers, owner = create_authenticated_user(client, db)
    outsider_headers, _ = create_authenticated_user(client, db)

    group = create_group(client, owner_headers)
    message = create_message(db, group["id"], owner.id)

    response = client.get(
        f"/api/v1/groups/{group['id']}/messages/"
        f"{message.id}/reactions",
        headers=outsider_headers,
    )

    assert response.status_code == 403


def test_wrong_group_message_path_returns_not_found(client, db):
    headers, user = create_authenticated_user(client, db)
    group = create_group(client, headers)
    message = create_message(db, group["id"], user.id)

    response = client.get(
        f"/api/v1/groups/{uuid4()}/messages/"
        f"{message.id}/reactions",
        headers=headers,
    )

    assert response.status_code == 404