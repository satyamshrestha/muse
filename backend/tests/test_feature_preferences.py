from uuid import uuid4


def create_authenticated_user(client):
    email = f"{uuid4().hex}@example.com"
    password = "Password123!"

    signup = client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "password": password,
            "display_name": "Feature Preference API Test",
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
    return {"Authorization": f"Bearer {token}"}


def test_get_feature_preferences_requires_authentication(client):
    response = client.get("/api/v1/feature-preferences")

    assert response.status_code == 401


def test_replace_feature_preferences_requires_authentication(client):
    response = client.put(
        "/api/v1/feature-preferences",
        json={"feature_preferences": {"daily_drop": "high"}},
    )

    assert response.status_code == 401


def test_replace_and_get_feature_preferences(client):
    headers = create_authenticated_user(client)

    replace_response = client.put(
        "/api/v1/feature-preferences",
        headers=headers,
        json={
            "feature_preferences": {
                "daily_drop": "high",
                "games": "medium",
            }
        },
    )

    assert replace_response.status_code == 200
    assert {
        item["feature"]: item["preference"]
        for item in replace_response.json()["feature_preferences"]
    } == {
        "daily_drop": "high",
        "games": "medium",
    }

    get_response = client.get(
        "/api/v1/feature-preferences",
        headers=headers,
    )

    assert get_response.status_code == 200
    assert {
        item["feature"]: item["preference"]
        for item in get_response.json()["feature_preferences"]
    } == {
        "daily_drop": "high",
        "games": "medium",
    }


def test_replacement_removes_old_preferences(client):
    headers = create_authenticated_user(client)

    first_response = client.put(
        "/api/v1/feature-preferences",
        headers=headers,
        json={
            "feature_preferences": {
                "daily_drop": "high",
                "games": "medium",
            }
        },
    )
    assert first_response.status_code == 200

    second_response = client.put(
        "/api/v1/feature-preferences",
        headers=headers,
        json={
            "feature_preferences": {
                "recommendations": "low",
            }
        },
    )

    assert second_response.status_code == 200
    assert second_response.json()["feature_preferences"] == [
        {"feature": "recommendations", "preference": "low"}
    ]


def test_empty_preferences_clear_existing_values(client):
    headers = create_authenticated_user(client)

    initial_response = client.put(
        "/api/v1/feature-preferences",
        headers=headers,
        json={
            "feature_preferences": {"daily_drop": "high"}
        },
    )
    assert initial_response.status_code == 200

    clear_response = client.put(
        "/api/v1/feature-preferences",
        headers=headers,
        json={"feature_preferences": {}},
    )

    assert clear_response.status_code == 200
    assert clear_response.json()["feature_preferences"] == []


def test_invalid_feature_preference_returns_422(client):
    headers = create_authenticated_user(client)

    response = client.put(
        "/api/v1/feature-preferences",
        headers=headers,
        json={
            "feature_preferences": {
                "daily_drop": "   ",
            }
        },
    )

    assert response.status_code == 422


def test_feature_preferences_are_isolated_between_users(client):
    first_headers = create_authenticated_user(client)
    second_headers = create_authenticated_user(client)

    first_response = client.put(
        "/api/v1/feature-preferences",
        headers=first_headers,
        json={
            "feature_preferences": {"daily_drop": "high"}
        },
    )
    assert first_response.status_code == 200

    second_response = client.put(
        "/api/v1/feature-preferences",
        headers=second_headers,
        json={
            "feature_preferences": {"games": "low"}
        },
    )
    assert second_response.status_code == 200

    first_get = client.get(
        "/api/v1/feature-preferences",
        headers=first_headers,
    )
    second_get = client.get(
        "/api/v1/feature-preferences",
        headers=second_headers,
    )

    assert first_get.status_code == 200
    assert first_get.json()["feature_preferences"] == [
        {"feature": "daily_drop", "preference": "high"}
    ]

    assert second_get.status_code == 200
    assert second_get.json()["feature_preferences"] == [
        {"feature": "games", "preference": "low"}
    ]