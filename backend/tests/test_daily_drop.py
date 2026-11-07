from datetime import date, timedelta
from uuid import uuid4

from app.models.user import User


def create_authenticated_user(client, db):
    email = f"{uuid4()}@example.com"
    password = "TestPassword123!"

    signup = client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "password": password,
            "display_name": "Daily Drop Tester",
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
    user = db.query(User).filter(User.email == email).first()

    return {"Authorization": f"Bearer {token}"}, user


def create_drop(client, headers, **overrides):
    payload = {
        "title": "Daily Inspiration",
        "content": "Keep moving forward.",
        "drop_date": date.today().isoformat(),
        "source": "system",
    }
    payload.update(overrides)

    return client.post(
        "/api/v1/daily-drops",
        headers=headers,
        json=payload,
    )


def test_create_daily_drop(client, db):
    headers, user = create_authenticated_user(client, db)

    response = create_drop(client, headers)

    assert response.status_code == 201

    data = response.json()
    assert data["title"] == "Daily Inspiration"
    assert data["content"] == "Keep moving forward."
    assert data["source"] == "system"
    assert data["user_id"] == str(user.id)
    assert data["drop_date"] == date.today().isoformat()


def test_create_daily_drop_rejects_empty_fields(client, db):
    headers, _ = create_authenticated_user(client, db)

    response = create_drop(
        client,
        headers,
        title="",
    )

    assert response.status_code == 422


def test_get_daily_drops(client, db):
    headers, _ = create_authenticated_user(client, db)

    create_drop(client, headers, title="First Drop")
    create_drop(client, headers, title="Second Drop")

    response = client.get(
        "/api/v1/daily-drops",
        headers=headers,
    )

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_daily_drops_returns_empty_list(client, db):
    headers, _ = create_authenticated_user(client, db)

    response = client.get(
        "/api/v1/daily-drops",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json() == []


def test_get_daily_drop_by_id(client, db):
    headers, _ = create_authenticated_user(client, db)

    created = create_drop(client, headers)
    drop_id = created.json()["id"]

    response = client.get(
        f"/api/v1/daily-drops/{drop_id}",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["id"] == drop_id


def test_get_daily_drop_returns_404_for_unknown_id(client, db):
    headers, _ = create_authenticated_user(client, db)

    response = client.get(
        f"/api/v1/daily-drops/{uuid4()}",
        headers=headers,
    )

    assert response.status_code == 404


def test_get_daily_drop_does_not_expose_another_users_drop(client, db):
    owner_headers, _ = create_authenticated_user(client, db)
    another_headers, _ = create_authenticated_user(client, db)

    created = create_drop(client, owner_headers)
    drop_id = created.json()["id"]

    response = client.get(
        f"/api/v1/daily-drops/{drop_id}",
        headers=another_headers,
    )

    assert response.status_code == 404


def test_get_daily_drops_by_date(client, db):
    headers, _ = create_authenticated_user(client, db)
    today = date.today()

    create_drop(client, headers, title="Today's Drop")
    create_drop(
        client,
        headers,
        title="Yesterday's Drop",
        drop_date=(today - timedelta(days=1)).isoformat(),
    )

    response = client.get(
        f"/api/v1/daily-drops/date/{today.isoformat()}",
        headers=headers,
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "Today's Drop"


def test_get_daily_drops_by_date_returns_empty_list(client, db):
    headers, _ = create_authenticated_user(client, db)

    target_date = date.today() - timedelta(days=30)

    response = client.get(
        f"/api/v1/daily-drops/date/{target_date.isoformat()}",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json() == []


def test_delete_daily_drop(client, db):
    headers, _ = create_authenticated_user(client, db)

    created = create_drop(client, headers)
    drop_id = created.json()["id"]

    response = client.delete(
        f"/api/v1/daily-drops/{drop_id}",
        headers=headers,
    )

    assert response.status_code == 204

    get_response = client.get(
        f"/api/v1/daily-drops/{drop_id}",
        headers=headers,
    )

    assert get_response.status_code == 404


def test_delete_does_not_allow_another_user_to_delete_drop(client, db):
    owner_headers, _ = create_authenticated_user(client, db)
    another_headers, _ = create_authenticated_user(client, db)

    created = create_drop(client, owner_headers)
    drop_id = created.json()["id"]

    response = client.delete(
        f"/api/v1/daily-drops/{drop_id}",
        headers=another_headers,
    )

    assert response.status_code == 404

    owner_response = client.get(
        f"/api/v1/daily-drops/{drop_id}",
        headers=owner_headers,
    )

    assert owner_response.status_code == 200


def test_daily_drop_requires_authentication(client):
    response = client.get("/api/v1/daily-drops")

    assert response.status_code == 401

def test_users_can_only_see_their_own_drops(client, db):
    owner_headers, _ = create_authenticated_user(client, db)
    another_headers, _ = create_authenticated_user(client, db)

    today = date.today()

    created = create_drop(
        client,
        owner_headers,
        title="Private Drop",
        drop_date=today.isoformat(),
    )
    assert created.status_code == 201, created.text

    listed = client.get(
        "/api/v1/daily-drops",
        headers=another_headers,
    )

    assert listed.status_code == 200
    assert listed.json() == []

    filtered = client.get(
        f"/api/v1/daily-drops/date/{today.isoformat()}",
        headers=another_headers,
    )

    assert filtered.status_code == 200
    assert filtered.json() == []