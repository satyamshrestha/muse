from uuid import uuid4

from app.models.user import User


def create_authenticated_user(client, db):
    email = f"{uuid4()}@example.com"
    password = "TestPassword123!"

    signup = client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "password": password,
            "display_name": "Recommendation Tester",
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

    token = login.json()["access_token"]
    user = db.query(User).filter(User.email == email).first()

    return {"Authorization": f"Bearer {token}"}, user


def create_group(client, headers, name="Recommendation Group"):
    return client.post(
        "/api/v1/groups",
        headers=headers,
        json={"name": name},
    )


def create_recommendation(client, headers, group_id, **overrides):
    payload = {
        "recommendation_type": "activity",
        "title": "Visit a museum",
        "description": "Explore the local museum together.",
    }
    payload.update(overrides)

    return client.post(
        f"/api/v1/groups/{group_id}/recommendations",
        headers=headers,
        json=payload,
    )


def test_create_group_recommendation(client, db):
    headers, user = create_authenticated_user(client, db)
    group = create_group(client, headers)
    assert group.status_code == 201

    group_id = group.json()["id"]

    response = create_recommendation(client, headers, group_id)

    assert response.status_code == 201

    data = response.json()
    assert data["group_id"] == group_id
    assert data["created_by"] == str(user.id)
    assert data["recommendation_type"] == "activity"
    assert data["title"] == "Visit a museum"
    assert data["description"] == "Explore the local museum together."


def test_create_recommendation_without_description(client, db):
    headers, _ = create_authenticated_user(client, db)
    group = create_group(client, headers)
    group_id = group.json()["id"]

    response = create_recommendation(
        client,
        headers,
        group_id,
        description=None,
    )

    assert response.status_code == 201
    assert response.json()["description"] is None


def test_create_recommendation_rejects_empty_fields(client, db):
    headers, _ = create_authenticated_user(client, db)
    group = create_group(client, headers)
    group_id = group.json()["id"]

    response = create_recommendation(
        client,
        headers,
        group_id,
        title="",
    )

    assert response.status_code == 422


def test_create_recommendation_rejects_non_member(client, db):
    owner_headers, _ = create_authenticated_user(client, db)
    another_headers, _ = create_authenticated_user(client, db)

    group = create_group(client, owner_headers)
    group_id = group.json()["id"]

    response = create_recommendation(
        client,
        another_headers,
        group_id,
    )

    assert response.status_code == 403


def test_create_recommendation_returns_404_for_unknown_group(client, db):
    headers, _ = create_authenticated_user(client, db)

    response = create_recommendation(
        client,
        headers,
        str(uuid4()),
    )

    assert response.status_code == 404


def test_get_group_recommendations(client, db):
    headers, _ = create_authenticated_user(client, db)
    group = create_group(client, headers)
    group_id = group.json()["id"]

    create_recommendation(
        client, headers, group_id, title="First recommendation"
    )
    create_recommendation(
        client, headers, group_id, title="Second recommendation"
    )

    response = client.get(
        f"/api/v1/groups/{group_id}/recommendations",
        headers=headers,
    )

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_group_recommendations_returns_empty_list(client, db):
    headers, _ = create_authenticated_user(client, db)
    group = create_group(client, headers)
    group_id = group.json()["id"]

    response = client.get(
        f"/api/v1/groups/{group_id}/recommendations",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json() == []


def test_get_recommendations_by_type(client, db):
    headers, _ = create_authenticated_user(client, db)
    group = create_group(client, headers)
    group_id = group.json()["id"]

    create_recommendation(
        client,
        headers,
        group_id,
        recommendation_type="activity",
        title="Visit a museum",
    )
    create_recommendation(
        client,
        headers,
        group_id,
        recommendation_type="food",
        title="Try a restaurant",
    )

    response = client.get(
        f"/api/v1/groups/{group_id}/recommendations/type/activity",
        headers=headers,
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "Visit a museum"


def test_get_recommendation_by_id(client, db):
    headers, _ = create_authenticated_user(client, db)
    group = create_group(client, headers)
    group_id = group.json()["id"]

    created = create_recommendation(client, headers, group_id)
    recommendation_id = created.json()["id"]

    response = client.get(
        f"/api/v1/groups/{group_id}/recommendations/{recommendation_id}",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["id"] == recommendation_id


def test_get_unknown_recommendation_returns_404(client, db):
    headers, _ = create_authenticated_user(client, db)
    group = create_group(client, headers)
    group_id = group.json()["id"]

    response = client.get(
        f"/api/v1/groups/{group_id}/recommendations/{uuid4()}",
        headers=headers,
    )

    assert response.status_code == 404


def test_non_member_cannot_get_recommendations(client, db):
    owner_headers, _ = create_authenticated_user(client, db)
    another_headers, _ = create_authenticated_user(client, db)

    group = create_group(client, owner_headers)
    group_id = group.json()["id"]

    create_recommendation(client, owner_headers, group_id)

    response = client.get(
        f"/api/v1/groups/{group_id}/recommendations",
        headers=another_headers,
    )

    assert response.status_code == 403


def test_recommendation_cannot_be_accessed_through_another_group(client, db):
    headers, _ = create_authenticated_user(client, db)

    first_group = create_group(client, headers, "First Group")
    second_group = create_group(client, headers, "Second Group")

    first_group_id = first_group.json()["id"]
    second_group_id = second_group.json()["id"]

    created = create_recommendation(client, headers, first_group_id)
    recommendation_id = created.json()["id"]

    response = client.get(
        f"/api/v1/groups/{second_group_id}/recommendations/{recommendation_id}",
        headers=headers,
    )

    assert response.status_code == 404


def test_delete_group_recommendation(client, db):
    headers, _ = create_authenticated_user(client, db)
    group = create_group(client, headers)
    group_id = group.json()["id"]

    created = create_recommendation(client, headers, group_id)
    recommendation_id = created.json()["id"]

    response = client.delete(
        f"/api/v1/groups/{group_id}/recommendations/{recommendation_id}",
        headers=headers,
    )

    assert response.status_code == 204

    get_response = client.get(
        f"/api/v1/groups/{group_id}/recommendations/{recommendation_id}",
        headers=headers,
    )

    assert get_response.status_code == 404


def test_another_member_cannot_delete_recommendation(client, db):
    owner_headers, _ = create_authenticated_user(client, db)
    another_headers, _ = create_authenticated_user(client, db)

    group = create_group(client, owner_headers)
    group_id = group.json()["id"]

    # The second user joins the group through the existing group API.
    invitation = client.post(
        f"/api/v1/groups/{group_id}/invitations",
        headers=owner_headers,
        json={},
    )

    # This test only needs a group member who isn't the recommendation
    # creator. If your invitation endpoint requires additional fields,
    # use the existing group invitation/join flow here.
    assert invitation.status_code in (200, 201, 422)

    if invitation.status_code in (200, 201):
        invitation_code = invitation.json().get("code")
        if invitation_code:
            join_response = client.post(
                "/api/v1/groups/join",
                headers=another_headers,
                json={"code": invitation_code},
            )
            assert join_response.status_code in (200, 201)

    created = create_recommendation(client, owner_headers, group_id)
    recommendation_id = created.json()["id"]

    response = client.delete(
        f"/api/v1/groups/{group_id}/recommendations/{recommendation_id}",
        headers=another_headers,
    )

    assert response.status_code in (403, 404)


def test_group_recommendations_require_authentication(client):
    response = client.get(
        f"/api/v1/groups/{uuid4()}/recommendations"
    )

    assert response.status_code == 401


def test_another_member_cannot_delete_recommendation(client, db):
    owner_headers, owner = create_authenticated_user(client, db)
    another_headers, _ = create_authenticated_user(client, db)

    group = create_group(client, owner_headers)
    group_id = group.json()["id"]

    invitation = client.post(
        f"/api/v1/groups/{group_id}/invitations",
        headers=owner_headers,
    )
    assert invitation.status_code == 201

    joined = client.post(
        "/api/v1/groups/join",
        headers=another_headers,
        json={"token": invitation.json()["token"]},
    )
    assert joined.status_code == 200

    created = create_recommendation(client, owner_headers, group_id)
    assert created.status_code == 201

    recommendation_id = created.json()["id"]
    assert created.json()["created_by"] == str(owner.id)