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
            "display_name": "Interaction Tester",
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


def create_recommendation(client, headers):
    response = client.post(
        "/api/v1/recommendations",
        headers=headers,
        json={
            "recommendation_type": "article",
            "title": "Learning Python",
            "source": "MUSE",
            "description": "A useful Python resource",
        },
    )
    assert response.status_code == 201
    return response.json()


def create_interaction(client, headers, recommendation_id, interaction_type="clicked"):
    response = client.post(
        "/api/v1/recommendation-interactions",
        headers=headers,
        json={
            "recommendation_id": recommendation_id,
            "interaction_type": interaction_type,
        },
    )
    return response


def test_create_recommendation_interaction(client, db):
    headers, user = create_authenticated_user(client, db)
    recommendation = create_recommendation(client, headers)

    response = create_interaction(
        client,
        headers,
        recommendation["id"],
        "clicked",
    )

    assert response.status_code == 201

    data = response.json()
    assert data["user_id"] == str(user.id)
    assert data["recommendation_id"] == recommendation["id"]
    assert data["interaction_type"] == "clicked"
    assert "id" in data
    assert "created_at" in data


def test_create_interaction_requires_authentication(client, db):
    headers, _ = create_authenticated_user(client, db)
    recommendation = create_recommendation(client, headers)

    response = client.post(
        "/api/v1/recommendation-interactions",
        json={
            "recommendation_id": recommendation["id"],
            "interaction_type": "clicked",
        },
    )

    assert response.status_code in (401, 403)


@pytest.mark.parametrize(
    "interaction_type",
    ["", " "],
)
def test_create_interaction_rejects_invalid_type(
    client,
    db,
    interaction_type,
):
    headers, _ = create_authenticated_user(client, db)
    recommendation = create_recommendation(client, headers)

    response = create_interaction(
        client,
        headers,
        recommendation["id"],
        interaction_type,
    )

    assert response.status_code == 422


def test_create_interaction_rejects_unknown_recommendation(client, db):
    headers, _ = create_authenticated_user(client, db)

    response = create_interaction(
        client,
        headers,
        str(uuid4()),
    )

    assert response.status_code == 404


def test_create_interaction_rejects_foreign_recommendation(client, db):
    owner_headers, _ = create_authenticated_user(client, db)
    other_headers, _ = create_authenticated_user(client, db)

    recommendation = create_recommendation(client, owner_headers)

    response = create_interaction(
        client,
        other_headers,
        recommendation["id"],
    )

    assert response.status_code == 404


def test_list_user_interactions(client, db):
    headers, _ = create_authenticated_user(client, db)
    recommendation = create_recommendation(client, headers)

    create_interaction(client, headers, recommendation["id"], "clicked")
    create_interaction(client, headers, recommendation["id"], "saved")

    response = client.get(
        "/api/v1/recommendation-interactions",
        headers=headers,
    )

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_list_interactions_returns_empty_list(client, db):
    headers, _ = create_authenticated_user(client, db)

    response = client.get(
        "/api/v1/recommendation-interactions",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json() == []


def test_list_interactions_requires_authentication(client):
    response = client.get("/api/v1/recommendation-interactions")

    assert response.status_code in (401, 403)


def test_list_interactions_isolated_by_user(client, db):
    first_headers, _ = create_authenticated_user(client, db)
    second_headers, _ = create_authenticated_user(client, db)

    recommendation = create_recommendation(client, first_headers)
    create_interaction(client, first_headers, recommendation["id"])

    response = client.get(
        "/api/v1/recommendation-interactions",
        headers=second_headers,
    )

    assert response.status_code == 200
    assert response.json() == []


def test_list_interactions_for_recommendation(client, db):
    headers, _ = create_authenticated_user(client, db)
    first_recommendation = create_recommendation(client, headers)
    second_recommendation = create_recommendation(client, headers)

    create_interaction(
        client,
        headers,
        first_recommendation["id"],
        "clicked",
    )
    create_interaction(
        client,
        headers,
        first_recommendation["id"],
        "saved",
    )
    create_interaction(
        client,
        headers,
        second_recommendation["id"],
        "dismissed",
    )

    response = client.get(
        f"/api/v1/recommendation-interactions/recommendation/{first_recommendation['id']}",
        headers=headers,
    )

    assert response.status_code == 200
    assert len(response.json()) == 2
    assert all(
        item["recommendation_id"] == first_recommendation["id"]
        for item in response.json()
    )


def test_list_interactions_for_unknown_recommendation(client, db):
    headers, _ = create_authenticated_user(client, db)

    response = client.get(
        f"/api/v1/recommendation-interactions/recommendation/{uuid4()}",
        headers=headers,
    )

    assert response.status_code == 404


def test_list_interactions_by_type(client, db):
    headers, _ = create_authenticated_user(client, db)
    recommendation = create_recommendation(client, headers)

    create_interaction(client, headers, recommendation["id"], "clicked")
    create_interaction(client, headers, recommendation["id"], "saved")
    create_interaction(client, headers, recommendation["id"], "clicked")

    response = client.get(
        "/api/v1/recommendation-interactions/type/clicked",
        headers=headers,
    )

    assert response.status_code == 200
    assert len(response.json()) == 2
    assert all(
        item["interaction_type"] == "clicked"
        for item in response.json()
    )


def test_list_interactions_by_type_returns_empty_list(client, db):
    headers, _ = create_authenticated_user(client, db)

    response = client.get(
        "/api/v1/recommendation-interactions/type/saved",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json() == []


def test_get_recommendation_interaction(client, db):
    headers, _ = create_authenticated_user(client, db)
    recommendation = create_recommendation(client, headers)

    created = create_interaction(
        client,
        headers,
        recommendation["id"],
    ).json()

    response = client.get(
        f"/api/v1/recommendation-interactions/{created['id']}",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_get_unknown_interaction_returns_404(client, db):
    headers, _ = create_authenticated_user(client, db)

    response = client.get(
        f"/api/v1/recommendation-interactions/{uuid4()}",
        headers=headers,
    )

    assert response.status_code == 404


def test_get_foreign_interaction_returns_404(client, db):
    owner_headers, _ = create_authenticated_user(client, db)
    other_headers, _ = create_authenticated_user(client, db)

    recommendation = create_recommendation(client, owner_headers)
    interaction = create_interaction(
        client,
        owner_headers,
        recommendation["id"],
    ).json()

    response = client.get(
        f"/api/v1/recommendation-interactions/{interaction['id']}",
        headers=other_headers,
    )

    assert response.status_code == 404


def test_delete_recommendation_interaction(client, db):
    headers, _ = create_authenticated_user(client, db)
    recommendation = create_recommendation(client, headers)

    interaction = create_interaction(
        client,
        headers,
        recommendation["id"],
    ).json()

    response = client.delete(
        f"/api/v1/recommendation-interactions/{interaction['id']}",
        headers=headers,
    )

    assert response.status_code == 204

    get_response = client.get(
        f"/api/v1/recommendation-interactions/{interaction['id']}",
        headers=headers,
    )

    assert get_response.status_code == 404


def test_delete_unknown_interaction_returns_404(client, db):
    headers, _ = create_authenticated_user(client, db)

    response = client.delete(
        f"/api/v1/recommendation-interactions/{uuid4()}",
        headers=headers,
    )

    assert response.status_code == 404


def test_delete_foreign_interaction_returns_404(client, db):
    owner_headers, _ = create_authenticated_user(client, db)
    other_headers, _ = create_authenticated_user(client, db)

    recommendation = create_recommendation(client, owner_headers)
    interaction = create_interaction(
        client,
        owner_headers,
        recommendation["id"],
    ).json()

    response = client.delete(
        f"/api/v1/recommendation-interactions/{interaction['id']}",
        headers=other_headers,
    )

    assert response.status_code == 404