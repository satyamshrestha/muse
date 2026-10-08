from uuid import uuid4

def test_create_group_rejects_empty_name(client):
    email = f"{uuid4()}@example.com"
    password = "Password123!"

    client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "password": password,
            "display_name": "Validation User",
        },
    )

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    access_token = login_response.json()["access_token"]

    response = client.post(
        "/api/v1/groups",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
        json={
            "name": "",
        },
    )

    assert response.status_code == 422