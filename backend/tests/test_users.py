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

    assert "access_token" in data
    assert "refresh_token" in data
    assert data["access_token"] != data["refresh_token"]
    assert data["token_type"] == "bearer"
    assert "password" not in data
    assert "password_hash" not in data

def test_get_me_success(client):
    signup_payload = {
        "email": "me@example.com",
        "password": "password123",
        "display_name": "Me User",
    }

    signup_response = client.post(
        "/api/v1/auth/signup",
        json=signup_payload,
    )

    assert signup_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "me@example.com",
            "password": "password123",
        },
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    me_response = client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert me_response.status_code == 200

    data = me_response.json()

    assert data["email"] == "me@example.com"
    assert data["display_name"] == "Me User"
    assert "id" in data
    assert "password" not in data
    assert "password_hash" not in data


def test_get_me_without_token_returns_401(client):
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401


def test_get_me_with_invalid_token_returns_401(client):
    response = client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": "Bearer invalid-token",
        },
    )

    assert response.status_code == 401

def test_refresh_token(client):
    signup_response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "refresh@example.com",
            "password": "password123",
            "display_name": "Refresh User",
        },
    )

    assert signup_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "refresh@example.com",
            "password": "password123",
        },
    )

    assert login_response.status_code == 200

    tokens = login_response.json()

    refresh_response = client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": tokens["refresh_token"],
        },
    )

    assert refresh_response.status_code == 200

    data = refresh_response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["refresh_token"] != tokens["refresh_token"]

    old_refresh_response = client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": tokens["refresh_token"],
        },
    )

    assert old_refresh_response.status_code == 401

    new_refresh_response = client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": data["refresh_token"],
        },
    )

    assert new_refresh_response.status_code == 200

def test_refresh_token_invalid(client):
    response = client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": "invalid-token",
        },
    )

    assert response.status_code == 401

def test_refresh_with_access_token_returns_401(client):
    signup_response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "wrong-token@example.com",
            "password": "password123",
            "display_name": "Wrong Token User",
        },
    )

    assert signup_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "wrong-token@example.com",
            "password": "password123",
        },
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    response = client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": access_token,
        },
    )

    assert response.status_code == 401

def test_logout_revokes_refresh_token(client):
    signup_response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "logout@example.com",
            "password": "password123",
            "display_name": "Logout User",
        },
    )

    assert signup_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "logout@example.com",
            "password": "password123",
        },
    )

    assert login_response.status_code == 200

    refresh_token = login_response.json()["refresh_token"]

    refresh_response = client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": refresh_token,
        },
    )

    assert refresh_response.status_code == 200

    rotated_refresh_token = refresh_response.json()["refresh_token"]

    logout_response = client.post(
        "/api/v1/auth/logout",
        json={
            "refresh_token": rotated_refresh_token,
        },
    )

    assert logout_response.status_code == 204

    revoked_refresh_response = client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": rotated_refresh_token,
        },
    )

    assert revoked_refresh_response.status_code == 401

def test_logout_with_invalid_refresh_token_returns_401(client):
    response = client.post(
        "/api/v1/auth/logout",
        json={
            "refresh_token": "invalid-token",
        },
    )

    assert response.status_code == 401

def test_logout_with_access_token_returns_401(client):
    signup_response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "logout-access@example.com",
            "password": "password123",
            "display_name": "Logout Access User",
        },
    )
    assert signup_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "logout-access@example.com",
            "password": "password123",
        },
    )
    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    response = client.post(
        "/api/v1/auth/logout",
        json={
            "refresh_token": access_token,
        },
    )

    assert response.status_code == 401

def test_update_me_success(client):
    signup_response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "update_me@example.com",
            "password": "password123",
            "display_name": "Old Name"
        }
    )

    assert signup_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "update_me@example.com",
            "password": "password123"
        }
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]
    
    response = client.patch(
        "/api/v1/auth/me",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
        json={
            "display_name": "New Name",
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["display_name"] == "New Name"
    assert data["email"] == "update_me@example.com"
    assert "password" not in data
    assert "password_hash" not in data

    me_response = client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": f"Bearer {access_token}",
        }
    )

    assert me_response.status_code == 200
    assert me_response.json()["display_name"] == "New Name"

def test_update_me_without_token_returns_401(client):
    response = client.patch(
        "/api/v1/auth/me",
        json={
            "display_name": "New Name",
        }
    )

    assert response.status_code == 401

def test_update_me_empty_display_name_returns_422(client):
    signup_response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "empty_name@example.com",
            "password": "password123",
            "display_name": "Old Name"
        }
    )

    assert signup_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "empty_name@example.com",
            "password": "password123"
        }
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]
    
    response = client.patch(
        "/api/v1/auth/me",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
        json={
            "display_name": "",
        }
    )

    assert response.status_code == 422

def test_update_me_bio_only(client):
    signup_response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "bio-only@example.com",
            "password": "password123",
            "display_name": "Original Name",
        },
    )

    assert signup_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "bio-only@example.com",
            "password": "password123",
        },
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    response = client.patch(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"bio": "Building AI systems."},
    )

    assert response.status_code == 200

    data = response.json()
    assert data["bio"] == "Building AI systems."
    assert data["display_name"] == "Original Name"

def test_update_me_display_name_and_bio(client):
    signup_response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "both-fields@example.com",
            "password": "password123",
            "display_name": "Old Name",
        },
    )

    assert signup_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "both-fields@example.com",
            "password": "password123",
        },
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    response = client.patch(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "display_name": "New Name",
            "bio": "Building AI systems.",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["display_name"] == "New Name"
    assert data["bio"] == "Building AI systems."

def test_update_me_empty_bio_returns_200(client):
    signup_response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "empty-bio@example.com",
            "password": "password123",
            "display_name": "Test User",
        },
    )

    assert signup_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "empty-bio@example.com",
            "password": "password123",
        },
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    response = client.patch(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"bio": ""},
    )

    assert response.status_code == 200
    assert response.json()["bio"] == ""

def test_update_me_bio_too_long_returns_422(client):
    signup_response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "long-bio@example.com",
            "password": "password123",
            "display_name": "Test User",
        },
    )

    assert signup_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "long-bio@example.com",
            "password": "password123",
        },
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    response = client.patch(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"bio": "a" * 501},
    )

    assert response.status_code == 422

def test_change_password_success(client):
    signup_response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "change-password@example.com",
            "password": "password123",
            "display_name": "Password User",
        },
    )

    assert signup_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "change-password@example.com",
            "password": "password123",
        },
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    response = client.patch(
        "/api/v1/auth/password",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
        json={
            "current_password": "password123",
            "new_password": "newpassword123",
        },
    )

    assert response.status_code == 204

    old_login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "change-password@example.com",
            "password": "password123",
        },
    )

    assert old_login_response.status_code == 401

    new_login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "change-password@example.com",
            "password": "newpassword123",
        },
    )

    assert new_login_response.status_code == 200


def test_change_password_wrong_current_password_returns_401(client):
    signup_response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "wrong-current@example.com",
            "password": "password123",
            "display_name": "Password User",
        },
    )

    assert signup_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "wrong-current@example.com",
            "password": "password123",
        },
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    response = client.patch(
        "/api/v1/auth/password",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
        json={
            "current_password": "wrong-password",
            "new_password": "newpassword123",
        },
    )

    assert response.status_code == 401


def test_change_password_without_token_returns_401(client):
    response = client.patch(
        "/api/v1/auth/password",
        json={
            "current_password": "password123",
            "new_password": "newpassword123",
        },
    )

    assert response.status_code == 401


def test_change_password_short_new_password_returns_422(client):
    signup_response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "short-password@example.com",
            "password": "password123",
            "display_name": "Password User",
        },
    )

    assert signup_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "short-password@example.com",
            "password": "password123",
        },
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    response = client.patch(
        "/api/v1/auth/password",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
        json={
            "current_password": "password123",
            "new_password": "short",
        },
    )

    assert response.status_code == 422