from uuid import uuid4

import pytest


def create_authenticated_user(client):
    email = f"{uuid4()}@example.com"
    password = "Password123!"

    signup = client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "password": password,
            "display_name": "Invitation API Tester",
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

    return {
        "Authorization": f"Bearer {login.json()['access_token']}"
    }


@pytest.mark.parametrize(
    "token",
    [
        "",
        "x" * 19,
        "x" * 201,
    ],
)
def test_join_group_rejects_token_outside_length_limits(
    client,
    token,
):
    headers = create_authenticated_user(client)

    response = client.post(
        "/api/v1/groups/join",
        headers=headers,
        json={"token": token},
    )

    assert response.status_code == 422


def test_join_group_rejects_missing_token(client):
    headers = create_authenticated_user(client)

    response = client.post(
        "/api/v1/groups/join",
        headers=headers,
        json={},
    )

    assert response.status_code == 422