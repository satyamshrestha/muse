def test_create_user(client):
    response = client.post(
        "/users",
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