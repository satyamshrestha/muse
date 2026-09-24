def test_create_user(client):
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "test@example.com",
            "password": "password123",
            "display_name": "Test User",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["email"] == "test@example.com"
    assert data["display_name"] == "Test User"
    assert "id" in data
    assert "password" not in data
    assert "password_hash" not in data


def test_create_duplicate_user_returns_409(client):
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
    assert second_response.json() == {
        "detail": "User already exists!"
    }


def test_login_success(client):
    signup_payload = {
        "email": "login@example.com",
        "password": "password123",
        "display_name": "Login User",
    }

    signup_response = client.post(
        "/api/v1/auth/signup",
        json=signup_payload,
    )

    assert signup_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "login@example.com",
            "password": "password123",
        },
    )

    assert login_response.status_code == 200

    data = login_response.json()

    assert data["email"] == "login@example.com"
    assert data["display_name"] == "Login User"
    assert "id" in data
    assert "password" not in data
    assert "password_hash" not in data


def test_login_wrong_password(client):
    signup_payload = {
        "email": "wrong-password@example.com",
        "password": "password123",
        "display_name": "Wrong Password User",
    }

    signup_response = client.post(
        "/api/v1/auth/signup",
        json=signup_payload,
    )

    assert signup_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "wrong-password@example.com",
            "password": "wrongpassword",
        },
    )

    assert login_response.status_code == 400
    assert "detail" in login_response.json()


def test_login_nonexistent_user(client):
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "does-not-exist@example.com",
            "password": "password123",
        },
    )

    assert login_response.status_code == 400
    assert "detail" in login_response.json()