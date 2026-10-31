from uuid import uuid4

from app.models.user import User


def create_authenticated_user(client, db):
    email = f"{uuid4()}@example.com"
    password = "Password123!"

    signup = client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "password": password,
            "display_name": "Signal Tester",
        },
    )
    assert signup.status_code == 201, signup.text

    login = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )
    assert login.status_code == 200, login.text

    user = db.query(User).filter(User.email == email).first()
    assert user is not None

    headers = {
        "Authorization": f"Bearer {login.json()['access_token']}"
    }

    return headers, user


def create_signal(client, headers, signal_type="mood", value="happy"):
    return client.post(
        "/api/v1/behavioral-signals",
        headers=headers,
        json={
            "signal_type": signal_type,
            "value": value,
        },
    )


def test_create_list_filter_and_delete_signals(client, db):
    headers, user = create_authenticated_user(client, db)

    first = create_signal(client, headers, "mood", "happy")
    assert first.status_code == 201, first.text

    second = create_signal(client, headers, "activity", "studied")
    assert second.status_code == 201, second.text

    assert first.json()["user_id"] == str(user.id)

    listed = client.get(
        "/api/v1/behavioral-signals",
        headers=headers,
    )

    assert listed.status_code == 200
    assert len(listed.json()) == 2

    filtered = client.get(
        "/api/v1/behavioral-signals/type/mood",
        headers=headers,
    )

    assert filtered.status_code == 200
    assert len(filtered.json()) == 1
    assert filtered.json()[0]["value"] == "happy"

    deleted = client.delete(
        f"/api/v1/behavioral-signals/{first.json()['id']}",
        headers=headers,
    )

    assert deleted.status_code == 204

    remaining = client.get(
        "/api/v1/behavioral-signals",
        headers=headers,
    )

    assert remaining.status_code == 200
    assert len(remaining.json()) == 1
    assert remaining.json()[0]["value"] == "studied"


def test_behavioral_signal_endpoints_require_authentication(client):
    response = client.get("/api/v1/behavioral-signals")

    assert response.status_code == 401


def test_create_signal_rejects_empty_fields(client, db):
    headers, _ = create_authenticated_user(client, db)

    response = create_signal(client, headers, "   ", "happy")

    assert response.status_code == 422


def test_user_cannot_delete_another_users_signal(client, db):
    owner_headers, _ = create_authenticated_user(client, db)

    signal = create_signal(client, owner_headers)
    assert signal.status_code == 201, signal.text

    another_headers, _ = create_authenticated_user(client, db)

    response = client.delete(
        f"/api/v1/behavioral-signals/{signal.json()['id']}",
        headers=another_headers,
    )

    assert response.status_code == 403


def test_delete_missing_signal_returns_404(client, db):
    headers, _ = create_authenticated_user(client, db)

    response = client.delete(
        f"/api/v1/behavioral-signals/{uuid4()}",
        headers=headers,
    )

    assert response.status_code == 404


def test_filter_signals_with_no_matches_returns_empty_list(client, db):
    headers, _ = create_authenticated_user(client, db)

    response = client.get(
        "/api/v1/behavioral-signals/type/nonexistent",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json() == []