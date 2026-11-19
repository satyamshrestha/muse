def test_signup_duplicate_email_returns_409(client):
    payload = {
        "email": "duplicate@example.com",
        "password": "password123",
        "display_name": "Test User",
    }

    first_response = client.post(
        "/api/v1/auth/signup",
        json=payload,
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/api/v1/auth/signup",
        json=payload,
    )

    assert second_response.status_code == 409


def test_signup_invalid_email_returns_422(client):
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "not-an-email",
            "password": "password123",
            "display_name": "Test User",
        },
    )

    assert response.status_code == 422


def test_signup_short_password_returns_422(client):
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "short-password@example.com",
            "password": "short",
            "display_name": "Test User",
        },
    )

    assert response.status_code == 422


def test_signup_empty_display_name_returns_422(client):
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "empty-name@example.com",
            "password": "password123",
            "display_name": "",
        },
    )

    assert response.status_code == 422


def test_signup_display_name_too_long_returns_422(client):
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "long-name@example.com",
            "password": "password123",
            "display_name": "a" * 101,
        },
    )

    assert response.status_code == 422


def test_login_wrong_password_returns_401(client):
    signup_response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "wrong-login@example.com",
            "password": "password123",
            "display_name": "Test User",
        },
    )

    assert signup_response.status_code == 201

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "wrong-login@example.com",
            "password": "wrongpassword123",
        },
    )

    assert response.status_code == 401