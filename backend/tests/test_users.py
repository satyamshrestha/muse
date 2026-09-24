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

    first_response = client.post("/api/v1/auth/signup", json=payload)
    assert first_response.status_code == 201

    second_response = client.post("/api/v1/auth/signup", json=payload)

    assert second_response.status_code == 409
    assert second_response.json() == {
        "detail": "User already exists!"
    }