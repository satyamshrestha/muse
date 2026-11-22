from uuid import uuid4

import pytest

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


@pytest.mark.parametrize(
    "payload",
    [
        {
            "recommendation_type": "activity",
            "source": "ai",
        },
        {
            "title": "Try photography",
            "source": "ai",
        },
        {
            "recommendation_type": "activity",
            "title": "Try photography",
        },
    ],
)
def test_create_recommendation_rejects_missing_required_fields(
    client,
    db,
    payload,
):
    headers, _ = create_authenticated_user(client, db)

    response = client.post(
        "/api/v1/recommendations",
        json=payload,
        headers=headers,
    )

    assert response.status_code == 422


@pytest.mark.parametrize(
    "field",
    [
        "recommendation_type",
        "title",
        "source",
    ],
)
def test_create_recommendation_rejects_empty_required_string(
    client,
    db,
    field,
):
    headers, _ = create_authenticated_user(client, db)

    response = create_recommendation(
        client,
        headers,
        **{field: ""},
    )

    assert response.status_code == 422


@pytest.mark.parametrize(
    "field",
    [
        "recommendation_type",
        "title",
        "source",
    ],
)
def test_create_recommendation_rejects_whitespace_required_string(
    client,
    db,
    field,
):
    headers, _ = create_authenticated_user(client, db)

    response = create_recommendation(
        client,
        headers,
        **{field: "   "},
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


@pytest.mark.parametrize(
    ("field", "maximum"),
    [
        ("recommendation_type", 100),
        ("title", 255),
        ("source", 100),
    ],
)
def test_create_recommendation_accepts_maximum_field_length(
    client,
    db,
    field,
    maximum,
):
    headers, _ = create_authenticated_user(client, db)

    response = create_recommendation(
        client,
        headers,
        **{field: "a" * maximum},
    )

    assert response.status_code == 201
    assert response.json()[field] == "a" * maximum


@pytest.mark.parametrize(
    ("field", "maximum"),
    [
        ("recommendation_type", 100),
        ("title", 255),
        ("source", 100),
    ],
)
def test_create_recommendation_rejects_excessive_field_length(
    client,
    db,
    field,
    maximum,
):
    headers, _ = create_authenticated_user(client, db)

    response = create_recommendation(
        client,
        headers,
        **{field: "a" * (maximum + 1)},
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


def test_list_recommendations_requires_authentication(client):
    response = client.get("/api/v1/recommendations")

    assert response.status_code == 401


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


@pytest.mark.parametrize("method", ["get", "delete"])
def test_recommendation_id_endpoints_reject_malformed_uuid(
    client,
    db,
    method,
):
    headers, _ = create_authenticated_user(client, db)

    response = getattr(client, method)(
        "/api/v1/recommendations/not-a-uuid",
        headers=headers,
    )

    assert response.status_code == 422


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


def test_filter_recommendations_by_type_requires_authentication(client):
    response = client.get(
        "/api/v1/recommendations/type/activity",
    )

    assert response.status_code == 401


def test_filter_recommendations_by_type_only_returns_current_users_data(
    client,
    db,
):
    headers_one, _ = create_authenticated_user(client, db)
    headers_two, _ = create_authenticated_user(client, db)

    create_recommendation(
        client,
        headers_one,
        recommendation_type="activity",
        title="User One activity",
    )
    create_recommendation(
        client,
        headers_two,
        recommendation_type="activity",
        title="User Two activity",
    )

    response = client.get(
        "/api/v1/recommendations/type/activity",
        headers=headers_one,
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "User One activity"


def test_filter_recommendations_by_type_rejects_empty_value(
    client,
    db,
):
    headers, _ = create_authenticated_user(client, db)

    response = client.get(
        "/api/v1/recommendations/type/%20%20%20",
        headers=headers,
    )

    assert response.status_code == 422


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


def test_filter_recommendations_by_source_requires_authentication(client):
    response = client.get(
        "/api/v1/recommendations/source/ai",
    )

    assert response.status_code == 401


def test_filter_recommendations_by_source_only_returns_current_users_data(
    client,
    db,
):
    headers_one, _ = create_authenticated_user(client, db)
    headers_two, _ = create_authenticated_user(client, db)

    create_recommendation(
        client,
        headers_one,
        source="ai",
        title="User One recommendation",
    )
    create_recommendation(
        client,
        headers_two,
        source="ai",
        title="User Two recommendation",
    )

    response = client.get(
        "/api/v1/recommendations/source/ai",
        headers=headers_one,
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "User One recommendation"


def test_filter_recommendations_by_source_rejects_empty_value(
    client,
    db,
):
    headers, _ = create_authenticated_user(client, db)

    response = client.get(
        "/api/v1/recommendations/source/%20%20%20",
        headers=headers,
    )

    assert response.status_code == 422


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


def test_delete_recommendation_not_found(client, db):
    headers, _ = create_authenticated_user(client, db)

    response = client.delete(
        f"/api/v1/recommendations/{uuid4()}",
        headers=headers,
    )

    assert response.status_code == 404


def test_delete_recommendation_requires_authentication(client):
    response = client.delete(
        f"/api/v1/recommendations/{uuid4()}",
    )

    assert response.status_code == 401


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