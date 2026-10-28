from uuid import uuid4

from app.models.user import User


def create_authenticated_user(client, db):
    email = f"{uuid4()}@example.com"
    password = "Password123!"

    signup = client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "password": password,
            "display_name": "Plan Participant Tester",
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
    result = client.post(
        "/api/v1/groups",
        headers=headers,
        json={"name": f"Participant Test Group {uuid4()}"},
    )
    assert result.status_code == 201, result.text
    return result.json()


def add_group_member(client, group_id, owner_headers, member_headers):
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


def create_plan(client, headers, group_id):
    result = client.post(
        f"/api/v1/groups/{group_id}/plans",
        headers=headers,
        json={"title": "Participant Test Plan"},
    )
    assert result.status_code == 201, result.text
    return result.json()


def test_invite_list_respond_and_remove_participant(client, db):
    owner_headers, _ = create_authenticated_user(client, db)
    member_headers, member = create_authenticated_user(client, db)

    group = create_group(client, owner_headers)
    add_group_member(
        client,
        group["id"],
        owner_headers,
        member_headers,
    )
    plan = create_plan(client, owner_headers, group["id"])

    base = (
        f"/api/v1/groups/{group['id']}/plans/"
        f"{plan['id']}/participants"
    )

    invited = client.post(
        base,
        headers=owner_headers,
        json={"user_id": str(member.id)},
    )
    assert invited.status_code == 201, invited.text
    assert invited.json()["status"] == "invited"

    listing = client.get(base, headers=owner_headers)
    assert listing.status_code == 200, listing.text
    assert len(listing.json()) == 1
    assert listing.json()[0]["user_id"] == str(member.id)

    response = client.put(
        f"{base}/me",
        headers=member_headers,
        json={"status": "accepted"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "accepted"

    deleted = client.delete(
        f"{base}/{member.id}",
        headers=owner_headers,
    )
    assert deleted.status_code == 204

    listing_after_delete = client.get(base, headers=owner_headers)
    assert listing_after_delete.status_code == 200
    assert listing_after_delete.json() == []


def test_participant_endpoints_require_authentication(client, db):
    owner_headers, _ = create_authenticated_user(client, db)
    group = create_group(client, owner_headers)
    plan = create_plan(client, owner_headers, group["id"])

    base = (
        f"/api/v1/groups/{group['id']}/plans/"
        f"{plan['id']}/participants"
    )

    result = client.get(base)

    assert result.status_code == 401


def test_non_member_cannot_list_participants(client, db):
    owner_headers, _ = create_authenticated_user(client, db)
    outsider_headers, _ = create_authenticated_user(client, db)

    group = create_group(client, owner_headers)
    plan = create_plan(client, owner_headers, group["id"])

    result = client.get(
        f"/api/v1/groups/{group['id']}/plans/"
        f"{plan['id']}/participants",
        headers=outsider_headers,
    )

    assert result.status_code == 403


def test_duplicate_invitation_returns_conflict(client, db):
    owner_headers, _ = create_authenticated_user(client, db)
    member_headers, member = create_authenticated_user(client, db)

    group = create_group(client, owner_headers)
    add_group_member(
        client,
        group["id"],
        owner_headers,
        member_headers,
    )
    plan = create_plan(client, owner_headers, group["id"])

    base = (
        f"/api/v1/groups/{group['id']}/plans/"
        f"{plan['id']}/participants"
    )
    payload = {"user_id": str(member.id)}

    first = client.post(base, headers=owner_headers, json=payload)
    assert first.status_code == 201, first.text

    second = client.post(base, headers=owner_headers, json=payload)
    assert second.status_code == 409, second.text


def test_invalid_participant_status_returns_validation_error(client, db):
    owner_headers, _ = create_authenticated_user(client, db)
    group = create_group(client, owner_headers)
    plan = create_plan(client, owner_headers, group["id"])

    result = client.put(
        f"/api/v1/groups/{group['id']}/plans/"
        f"{plan['id']}/participants/me",
        headers=owner_headers,
        json={"status": "maybe"},
    )

    assert result.status_code == 422