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
            "display_name": "Plan API Tester",
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


def create_group(client, headers, name="Plan Test Group"):
    result = client.post(
        "/api/v1/groups",
        headers=headers,
        json={"name": name},
    )
    assert result.status_code == 201, result.text
    return result.json()


def create_plan(client, headers, group_id, title="Test Plan"):
    result = client.post(
        f"/api/v1/groups/{group_id}/plans",
        headers=headers,
        json={
            "title": title,
            "description": "Plan API integration test",
            "starts_at": "2026-11-01T10:00:00Z",
            "ends_at": "2026-11-01T12:00:00Z",
        },
    )
    assert result.status_code == 201, result.text
    return result.json()


def test_create_get_and_list_plans(client, db):
    headers, _ = create_authenticated_user(client, db)
    group = create_group(client, headers)

    created = create_plan(client, headers, group["id"])

    assert created["title"] == "Test Plan"
    assert created["group_id"] == group["id"]
    assert created["starts_at"] is not None
    assert created["ends_at"] is not None
    assert created["created_by"]

    fetched = client.get(
        f"/api/v1/groups/{group['id']}/plans/{created['id']}",
        headers=headers,
    )
    assert fetched.status_code == 200, fetched.text
    assert fetched.json()["id"] == created["id"]

    listing = client.get(
        f"/api/v1/groups/{group['id']}/plans",
        headers=headers,
    )
    assert listing.status_code == 200, listing.text
    assert [item["id"] for item in listing.json()] == [created["id"]]


def test_plan_endpoints_require_authentication(client, db):
    headers, _ = create_authenticated_user(client, db)
    group = create_group(client, headers)
    plan = create_plan(client, headers, group["id"])

    listing = client.get(
        f"/api/v1/groups/{group['id']}/plans",
    )
    fetching = client.get(
        f"/api/v1/groups/{group['id']}/plans/{plan['id']}",
    )

    assert listing.status_code == 401
    assert fetching.status_code == 401


def test_non_member_cannot_access_plans(client, db):
    owner_headers, _ = create_authenticated_user(client, db)
    outsider_headers, _ = create_authenticated_user(client, db)

    group = create_group(client, owner_headers)
    plan = create_plan(client, owner_headers, group["id"])

    listing = client.get(
        f"/api/v1/groups/{group['id']}/plans",
        headers=outsider_headers,
    )
    fetching = client.get(
        f"/api/v1/groups/{group['id']}/plans/{plan['id']}",
        headers=outsider_headers,
    )

    assert listing.status_code == 403
    assert fetching.status_code == 403


def test_create_plan_rejects_invalid_schedule(client, db):
    headers, _ = create_authenticated_user(client, db)
    group = create_group(client, headers)

    result = client.post(
        f"/api/v1/groups/{group['id']}/plans",
        headers=headers,
        json={
            "title": "Invalid Schedule",
            "starts_at": "2026-11-01T12:00:00Z",
            "ends_at": "2026-11-01T10:00:00Z",
        },
    )

    assert result.status_code == 422


def test_update_and_delete_plan(client, db):
    headers, _ = create_authenticated_user(client, db)
    group = create_group(client, headers)
    plan = create_plan(client, headers, group["id"])

    updated = client.put(
        f"/api/v1/groups/{group['id']}/plans/{plan['id']}",
        headers=headers,
        json={
            "title": "Updated Plan",
            "description": "Updated description",
            "starts_at": "2026-11-02T10:00:00Z",
            "ends_at": "2026-11-02T11:00:00Z",
        },
    )

    assert updated.status_code == 200, updated.text
    assert updated.json()["title"] == "Updated Plan"
    assert updated.json()["description"] == "Updated description"

    deleted = client.delete(
        f"/api/v1/groups/{group['id']}/plans/{plan['id']}",
        headers=headers,
    )
    assert deleted.status_code == 204

    fetched = client.get(
        f"/api/v1/groups/{group['id']}/plans/{plan['id']}",
        headers=headers,
    )
    assert fetched.status_code == 404


def test_only_plan_creator_can_update_or_delete(client, db):
    owner_headers, _ = create_authenticated_user(client, db)
    member_headers, _ = create_authenticated_user(client, db)

    group = create_group(client, owner_headers)

    invitation = client.post(
        f"/api/v1/groups/{group['id']}/invitations",
        headers=owner_headers,
    )
    assert invitation.status_code == 201, invitation.text

    joined = client.post(
        "/api/v1/groups/join",
        headers=member_headers,
        json={"token": invitation.json()["token"]},
    )
    assert joined.status_code == 200, joined.text

    plan = create_plan(client, owner_headers, group["id"])

    update = client.put(
        f"/api/v1/groups/{group['id']}/plans/{plan['id']}",
        headers=member_headers,
        json={
            "title": "Unauthorized Update",
            "description": None,
            "starts_at": None,
            "ends_at": None,
        },
    )
    delete = client.delete(
        f"/api/v1/groups/{group['id']}/plans/{plan['id']}",
        headers=member_headers,
    )

    assert update.status_code == 403
    assert delete.status_code == 403


def test_list_plans_rejects_invalid_pagination(client, db):
    headers, _ = create_authenticated_user(client, db)
    group = create_group(client, headers)

    result = client.get(
        f"/api/v1/groups/{group['id']}/plans?limit=0",
        headers=headers,
    )

    assert result.status_code == 422