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
        json={"email": email, "password": password},
    )
    assert login.status_code == 200

    token = login.json()["access_token"]
    user = db.query(User).filter(User.email == email).first()

    return {"Authorization": f"Bearer {token}"}, user


def create_recommendation(client, headers, **overrides):
    payload = {
        "recommendation_type": "activity",
        "title": "Try a new hobby",
        "description": "Explore photography this weekend",
        "source": "ai",
    }
    payload.update(overrides)

    return client.post(
        "/api/v1/recommendations",
        json=payload,
        headers=headers,
    )


def test_create_recommendation(client, db):
    headers, user = create_authenticated_user(client, db)

    response = create_recommendation(client, headers)

    assert response.status_code == 201

    data = response.json()
    assert data["user_id"] == str(user.id)
    assert data["recommendation_type"] == "activity"
    assert data["title"] == "Try a new hobby"
    assert data["description"] == "Explore photography this weekend"
    assert data["source"] == "ai"
    assert "id" in data
    assert "created_at" in data


def test_create_recommendation_without_description(client, db):
    headers, _ = create_authenticated_user(client, db)

    response = create_recommendation(
        client,
        headers,
        description=None,
    )

    assert response.status_code == 201
    assert response.json()["description"] is None


def test_create_recommendation_requires_authentication(client):
    response = client.post(
        "/api/v1/recommendations",
        json={
            "recommendation_type": "activity",
            "title": "Try photography",
            "source": "ai",
        },
    )

    assert response.status_code == 401


def test_create_recommendation_rejects_missing_title(client, db):
    headers, _ = create_authenticated_user(client, db)

    response = client.post(
        "/api/v1/recommendations",
        json={
            "recommendation_type": "activity",
            "source": "ai",
        },
        headers=headers,
    )

    assert response.status_code == 422


def test_create_recommendation_rejects_empty_description(client, db):
    headers, _ = create_authenticated_user(client, db)

    response = create_recommendation(
        client,
        headers,
        description="   ",
    )

    assert response.status_code == 422


def test_list_recommendations(client, db):
    headers, _ = create_authenticated_user(client, db)

    create_recommendation(client, headers)
    create_recommendation(
        client,
        headers,
        title="Read a book",
        recommendation_type="learning",
    )

    response = client.get(
        "/api/v1/recommendations",
        headers=headers,
    )

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_list_recommendations_only_returns_current_users_data(client, db):
    headers_one, _ = create_authenticated_user(client, db)
    headers_two, _ = create_authenticated_user(client, db)

    create_recommendation(client, headers_one, title="User One")
    create_recommendation(client, headers_two, title="User Two")

    response = client.get(
        "/api/v1/recommendations",
        headers=headers_one,
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "User One"


def test_get_recommendation(client, db):
    headers, _ = create_authenticated_user(client, db)

    created = create_recommendation(client, headers)
    recommendation_id = created.json()["id"]

    response = client.get(
        f"/api/v1/recommendations/{recommendation_id}",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["id"] == recommendation_id


def test_get_recommendation_not_found(client, db):
    headers, _ = create_authenticated_user(client, db)

    response = client.get(
        f"/api/v1/recommendations/{uuid4()}",
        headers=headers,
    )

    assert response.status_code == 404


def test_get_recommendation_rejects_another_users_record(client, db):
    owner_headers, _ = create_authenticated_user(client, db)
    other_headers, _ = create_authenticated_user(client, db)

    created = create_recommendation(client, owner_headers)
    recommendation_id = created.json()["id"]

    response = client.get(
        f"/api/v1/recommendations/{recommendation_id}",
        headers=other_headers,
    )

    assert response.status_code == 404


def test_filter_recommendations_by_type(client, db):
    headers, _ = create_authenticated_user(client, db)

    create_recommendation(
        client,
        headers,
        recommendation_type="activity",
    )
    create_recommendation(
        client,
        headers,
        recommendation_type="learning",
    )
    create_recommendation(
        client,
        headers,
        recommendation_type="activity",
        title="Visit a museum",
    )

    response = client.get(
        "/api/v1/recommendations/type/activity",
        headers=headers,
    )

    assert response.status_code == 200
    assert len(response.json()) == 2
    assert all(
        item["recommendation_type"] == "activity"
        for item in response.json()
    )


def test_filter_recommendations_by_source(client, db):
    headers, _ = create_authenticated_user(client, db)

    create_recommendation(client, headers, source="ai")
    create_recommendation(client, headers, source="system")
    create_recommendation(
        client,
        headers,
        source="ai",
        title="Another AI recommendation",
    )

    response = client.get(
        "/api/v1/recommendations/source/ai",
        headers=headers,
    )

    assert response.status_code == 200
    assert len(response.json()) == 2
    assert all(
        item["source"] == "ai"
        for item in response.json()
    )


def test_delete_recommendation(client, db):
    headers, _ = create_authenticated_user(client, db)

    created = create_recommendation(client, headers)
    recommendation_id = created.json()["id"]

    response = client.delete(
        f"/api/v1/recommendations/{recommendation_id}",
        headers=headers,
    )

    assert response.status_code == 204

    get_response = client.get(
        f"/api/v1/recommendations/{recommendation_id}",
        headers=headers,
    )

    assert get_response.status_code == 404


def test_delete_recommendation_rejects_another_users_record(client, db):
    owner_headers, _ = create_authenticated_user(client, db)
    other_headers, _ = create_authenticated_user(client, db)

    created = create_recommendation(client, owner_headers)
    recommendation_id = created.json()["id"]

    response = client.delete(
        f"/api/v1/recommendations/{recommendation_id}",
        headers=other_headers,
    )

    assert response.status_code == 404

    # The original owner's recommendation must still exist.
    owner_response = client.get(
        f"/api/v1/recommendations/{recommendation_id}",
        headers=owner_headers,
    )

    assert owner_response.status_code == 200