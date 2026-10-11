from datetime import datetime, timedelta, timezone
from hashlib import sha256
from uuid import uuid4

from app.models.group_invitation import GroupInvitation


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
        json={"email": email, "password": password},
    )
    assert login.status_code == 200

    return {
        "Authorization": f"Bearer {login.json()['access_token']}"
    }


def create_group(client, headers, name="MUSE Crew"):
    response = client.post(
        "/api/v1/groups",
        headers=headers,
        json={"name": name},
    )
    assert response.status_code == 201
    return response.json()


def create_invitation(client, headers, group_id):
    response = client.post(
        f"/api/v1/groups/{group_id}/invitations",
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()


def redeem_invitation(client, headers, token):
    return client.post(
        "/api/v1/groups/join",
        headers=headers,
        json={"token": token},
    )


def revoke_invitation(client, headers, group_id, invitation_id):
    return client.delete(
        f"/api/v1/groups/{group_id}/invitations/{invitation_id}",
        headers=headers,
    )


def get_stored_invitation(db, group_id):
    return (
        db.query(GroupInvitation)
        .filter_by(group_id=group_id)
        .one()
    )


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
    create_group(client, headers, "My Group")

    response = client.get("/api/v1/groups", headers=headers)

    assert response.status_code == 200
    assert [group["name"] for group in response.json()] == ["My Group"]


def test_get_group_for_member(client):
    headers = create_authenticated_user(client)
    group = create_group(client, headers)

    response = client.get(
        f"/api/v1/groups/{group['id']}",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["id"] == group["id"]
    assert response.json()["name"] == "MUSE Crew"


def test_get_group_denies_non_member(client):
    owner_headers = create_authenticated_user(client)
    other_headers = create_authenticated_user(client)
    group = create_group(client, owner_headers, "Private Group")

    response = client.get(
        f"/api/v1/groups/{group['id']}",
        headers=other_headers,
    )

    assert response.status_code == 404


def test_list_groups_requires_authentication(client):
    response = client.get("/api/v1/groups")
    assert response.status_code == 401


def test_get_group_requires_authentication(client):
    response = client.get(f"/api/v1/groups/{uuid4()}")
    assert response.status_code == 401


def test_join_group_success(client):
    owner_headers = create_authenticated_user(client)
    member_headers = create_authenticated_user(client)
    group = create_group(client, owner_headers)
    invitation = create_invitation(
        client, owner_headers, group["id"]
    )

    response = redeem_invitation(
        client, member_headers, invitation["token"]
    )

    assert response.status_code == 200
    assert response.json()["id"] == group["id"]
    assert response.json()["name"] == "MUSE Crew"

    group_response = client.get(
        f"/api/v1/groups/{group['id']}",
        headers=member_headers,
    )
    assert group_response.status_code == 200

    list_response = client.get(
        "/api/v1/groups",
        headers=member_headers,
    )
    assert list_response.status_code == 200
    assert any(
        item["id"] == group["id"]
        for item in list_response.json()
    )


def test_join_group_rejects_invalid_invitation(client):
    headers = create_authenticated_user(client)

    response = redeem_invitation(client, headers, "x" * 32)

    assert response.status_code == 404


def test_join_group_rejects_reused_invitation(client):
    owner_headers = create_authenticated_user(client)
    first_member_headers = create_authenticated_user(client)
    second_member_headers = create_authenticated_user(client)
    group = create_group(client, owner_headers)
    invitation = create_invitation(
        client, owner_headers, group["id"]
    )

    first_response = redeem_invitation(
        client, first_member_headers, invitation["token"]
    )
    assert first_response.status_code == 200

    second_response = redeem_invitation(
        client, second_member_headers, invitation["token"]
    )
    assert second_response.status_code == 404


def test_join_group_rejects_duplicate_membership(client):
    owner_headers = create_authenticated_user(client)
    group = create_group(client, owner_headers)
    invitation = create_invitation(
        client, owner_headers, group["id"]
    )

    response = redeem_invitation(
        client, owner_headers, invitation["token"]
    )

    assert response.status_code == 409


def test_join_group_requires_authentication(client):
    response = client.post(
        "/api/v1/groups/join",
        json={"token": "x" * 32},
    )
    assert response.status_code == 401


def test_old_group_id_join_route_is_removed(client):
    headers = create_authenticated_user(client)
    group = create_group(client, headers)

    response = client.post(
        f"/api/v1/groups/{group['id']}/join",
        headers=headers,
    )

    assert response.status_code in (404, 405)


def test_create_invitation_requires_authentication(client):
    response = client.post(
        f"/api/v1/groups/{uuid4()}/invitations",
    )
    assert response.status_code == 401


def test_non_member_cannot_create_invitation(client):
    owner_headers = create_authenticated_user(client)
    other_headers = create_authenticated_user(client)
    group = create_group(client, owner_headers)

    response = client.post(
        f"/api/v1/groups/{group['id']}/invitations",
        headers=other_headers,
    )

    assert response.status_code == 404


def test_create_invitation_returns_token_and_expiry(client):
    headers = create_authenticated_user(client)
    group = create_group(client, headers)

    response = client.post(
        f"/api/v1/groups/{group['id']}/invitations",
        headers=headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert isinstance(data["token"], str)
    assert len(data["token"]) >= 32

    expires_at = datetime.fromisoformat(
        data["expires_at"].replace("Z", "+00:00")
    )
    now = datetime.now(timezone.utc)
    assert now + timedelta(days=6) < expires_at
    assert expires_at < now + timedelta(days=8)


def test_invitation_stores_only_token_hash(client, db):
    headers = create_authenticated_user(client)
    group = create_group(client, headers)

    response = client.post(
        f"/api/v1/groups/{group['id']}/invitations",
        headers=headers,
    )
    assert response.status_code == 201

    token = response.json()["token"]
    stored = get_stored_invitation(db, group["id"])

    assert stored.token_hash == sha256(
        token.encode("utf-8")
    ).hexdigest()
    assert stored.token_hash != token
    assert stored.revoked_at is None


def test_expired_invitation_cannot_be_redeemed(client, db):
    owner_headers = create_authenticated_user(client)
    member_headers = create_authenticated_user(client)
    group = create_group(client, owner_headers)
    invitation = create_invitation(
        client, owner_headers, group["id"]
    )

    stored = get_stored_invitation(db, group["id"])
    stored.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
    db.commit()

    response = redeem_invitation(
        client, member_headers, invitation["token"]
    )

    assert response.status_code == 404


def test_revoke_invitation_success(client, db):
    owner_headers = create_authenticated_user(client)
    group = create_group(client, owner_headers)
    create_invitation(client, owner_headers, group["id"])

    stored = get_stored_invitation(db, group["id"])

    response = revoke_invitation(
        client,
        owner_headers,
        group["id"],
        stored.id,
    )

    assert response.status_code == 204

    db.refresh(stored)
    assert stored.revoked_at is not None
    assert stored.redeemed_at is None


def test_revoked_invitation_cannot_be_redeemed(client, db):
    owner_headers = create_authenticated_user(client)
    member_headers = create_authenticated_user(client)
    group = create_group(client, owner_headers)
    invitation = create_invitation(
        client, owner_headers, group["id"]
    )

    stored = get_stored_invitation(db, group["id"])

    revoke_response = revoke_invitation(
        client,
        owner_headers,
        group["id"],
        stored.id,
    )
    assert revoke_response.status_code == 204

    redeem_response = redeem_invitation(
        client,
        member_headers,
        invitation["token"],
    )
    assert redeem_response.status_code == 404

    db.refresh(stored)
    assert stored.revoked_at is not None
    assert stored.redeemed_at is None


def test_non_member_cannot_revoke_invitation(client, db):
    owner_headers = create_authenticated_user(client)
    other_headers = create_authenticated_user(client)
    group = create_group(client, owner_headers)
    create_invitation(client, owner_headers, group["id"])

    stored = get_stored_invitation(db, group["id"])

    response = revoke_invitation(
        client,
        other_headers,
        group["id"],
        stored.id,
    )

    assert response.status_code == 404

    db.refresh(stored)
    assert stored.revoked_at is None


def test_revoke_invitation_requires_authentication(client):
    response = client.delete(
        f"/api/v1/groups/{uuid4()}/invitations/{uuid4()}",
    )

    assert response.status_code == 401


def test_revoke_invitation_rejects_unknown_invitation(client):
    headers = create_authenticated_user(client)
    group = create_group(client, headers)

    response = revoke_invitation(
        client,
        headers,
        group["id"],
        uuid4(),
    )

    assert response.status_code == 404


def test_revoke_invitation_rejects_already_revoked_invitation(
    client,
    db,
):
    headers = create_authenticated_user(client)
    group = create_group(client, headers)
    create_invitation(client, headers, group["id"])

    stored = get_stored_invitation(db, group["id"])

    first_response = revoke_invitation(
        client, headers, group["id"], stored.id
    )
    assert first_response.status_code == 204

    second_response = revoke_invitation(
        client, headers, group["id"], stored.id
    )
    assert second_response.status_code == 404


def test_revoke_invitation_rejects_already_redeemed_invitation(
    client,
    db,
):
    owner_headers = create_authenticated_user(client)
    member_headers = create_authenticated_user(client)
    group = create_group(client, owner_headers)
    invitation = create_invitation(
        client, owner_headers, group["id"]
    )

    redeem_response = redeem_invitation(
        client, member_headers, invitation["token"]
    )
    assert redeem_response.status_code == 200

    stored = get_stored_invitation(db, group["id"])

    revoke_response = revoke_invitation(
        client,
        owner_headers,
        group["id"],
        stored.id,
    )

    assert revoke_response.status_code == 404

    db.refresh(stored)
    assert stored.redeemed_at is not None
    assert stored.revoked_at is None


def test_revoking_one_invitation_does_not_invalidate_another(client, db):
    owner_headers = create_authenticated_user(client)
    first_member_headers = create_authenticated_user(client)
    second_member_headers = create_authenticated_user(client)
    group = create_group(client, owner_headers)

    first_invitation = create_invitation(client, owner_headers, group["id"])
    second_invitation = create_invitation(client, owner_headers, group["id"])

    first_hash = sha256(first_invitation["token"].encode("utf-8")).hexdigest()
    first_record = (
        db.query(GroupInvitation)
        .filter_by(token_hash=first_hash)
        .one()
    )

    revoke_response = revoke_invitation(
        client,
        owner_headers,
        group["id"],
        str(first_record.id),
    )
    assert revoke_response.status_code == 204

    first_join = redeem_invitation(
        client,
        first_member_headers,
        first_invitation["token"],
    )
    assert first_join.status_code == 404

    second_join = redeem_invitation(
        client,
        second_member_headers,
        second_invitation["token"],
    )
    assert second_join.status_code == 200


def test_get_group_members_returns_members_for_group_member(client):
    owner_headers = create_authenticated_user(client)
    second_member_headers = create_authenticated_user(client)
    group = create_group(client, owner_headers)
    invitation = create_invitation(
        client, owner_headers, group["id"]
    )

    joined = redeem_invitation(
        client, second_member_headers, invitation["token"]
    )
    assert joined.status_code == 200

    response = client.get(
        f"/api/v1/groups/{group['id']}/members",
        headers=owner_headers,
    )

    assert response.status_code == 200
    members = response.json()
    assert len(members) == 2
    assert len({member["id"] for member in members}) == 2
    assert {member["display_name"] for member in members} == {
        "Group Tester"
    }
    assert all("email" not in member for member in members)
    assert all("password_hash" not in member for member in members)


def test_get_group_members_denies_non_member(client):
    owner_headers = create_authenticated_user(client)
    other_headers = create_authenticated_user(client)
    group = create_group(client, owner_headers, "Private Group")

    response = client.get(
        f"/api/v1/groups/{group['id']}/members",
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
        f"/api/v1/groups/{uuid4()}/members"
    )
    assert response.status_code == 401


def test_leave_group_keeps_group_for_remaining_members(client):
    owner_headers = create_authenticated_user(client)
    member_headers = create_authenticated_user(client)
    group = create_group(client, owner_headers)
    invitation = create_invitation(
        client, owner_headers, group["id"]
    )

    joined = redeem_invitation(
        client, member_headers, invitation["token"]
    )
    assert joined.status_code == 200

    leave_response = client.delete(
        f"/api/v1/groups/{group['id']}/leave",
        headers=owner_headers,
    )
    assert leave_response.status_code == 204

    owner_group_response = client.get(
        f"/api/v1/groups/{group['id']}",
        headers=owner_headers,
    )
    assert owner_group_response.status_code == 404

    member_group_response = client.get(
        f"/api/v1/groups/{group['id']}",
        headers=member_headers,
    )
    assert member_group_response.status_code == 200

    members_response = client.get(
        f"/api/v1/groups/{group['id']}/members",
        headers=member_headers,
    )
    assert members_response.status_code == 200
    assert len(members_response.json()) == 1


def test_last_member_leaving_deletes_group(client):
    headers = create_authenticated_user(client)
    group = create_group(client, headers, "Temporary Group")

    leave_response = client.delete(
        f"/api/v1/groups/{group['id']}/leave",
        headers=headers,
    )
    assert leave_response.status_code == 204

    group_response = client.get(
        f"/api/v1/groups/{group['id']}",
        headers=headers,
    )
    assert group_response.status_code == 404

    groups_response = client.get(
        "/api/v1/groups",
        headers=headers,
    )
    assert groups_response.status_code == 200
    assert all(
        item["id"] != group["id"]
        for item in groups_response.json()
    )


def test_non_member_cannot_leave_group(client):
    owner_headers = create_authenticated_user(client)
    other_headers = create_authenticated_user(client)
    group = create_group(client, owner_headers)

    response = client.delete(
        f"/api/v1/groups/{group['id']}/leave",
        headers=other_headers,
    )

    assert response.status_code == 404


def test_leaving_unknown_group_returns_404(client):
    headers = create_authenticated_user(client)

    response = client.delete(
        f"/api/v1/groups/{uuid4()}/leave",
        headers=headers,
    )

    assert response.status_code == 404


def test_leaving_group_requires_authentication(client):
    response = client.delete(
        f"/api/v1/groups/{uuid4()}/leave"
    )
    assert response.status_code == 401