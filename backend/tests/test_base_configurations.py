from uuid import uuid4

from app.models.base_configuration import BaseConfiguration
from app.models.user import User


def create_authenticated_user(client):
    email = f"{uuid4()}@example.com"
    password = "Password123!"

    signup = client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "password": password,
            "display_name": "Configuration Tester",
        },
    )
    assert signup.status_code == 201, signup.text

    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login.status_code == 200, login.text

    return {
        "Authorization": f"Bearer {login.json()['access_token']}"
    }


def clear_configurations(db):
    db.query(User).update(
        {User.base_configuration_id: None},
        synchronize_session=False,
    )
    db.query(BaseConfiguration).delete(
        synchronize_session=False
    )
    db.commit()


def create_configuration(
    db,
    name: str,
    interests: list[str] | None = None,
    preferences: dict | None = None,
):
    configuration = BaseConfiguration(
        name=name,
        interests=interests or [],
        preferences=preferences or {},
    )

    db.add(configuration)
    db.commit()
    db.refresh(configuration)

    return configuration


def test_list_base_configurations(client, db):
    clear_configurations(db)
    headers = create_authenticated_user(client)

    first = create_configuration(
        db,
        name="AI Configuration",
        interests=["AI", "coding"],
        preferences={"theme": "dark"},
    )
    second = create_configuration(
        db,
        name="Gaming Configuration",
        interests=["gaming"],
        preferences={"theme": "light"},
    )

    result = client.get(
        "/api/v1/base-configurations",
        headers=headers,
    )

    assert result.status_code == 200, result.text

    data = result.json()

    assert len(data) == 2
    assert [item["name"] for item in data] == [
        "AI Configuration",
        "Gaming Configuration",
    ]

    first_result = next(
        item for item in data if item["id"] == str(first.id)
    )

    assert first_result["interests"] == ["AI", "coding"]
    assert first_result["preferences"] == {"theme": "dark"}
    assert first_result["created_at"]


def test_list_base_configurations_returns_empty_list(client, db):
    clear_configurations(db)
    headers = create_authenticated_user(client)

    result = client.get(
        "/api/v1/base-configurations",
        headers=headers,
    )

    assert result.status_code == 200
    assert result.json() == []


def test_get_base_configuration(client, db):
    clear_configurations(db)
    headers = create_authenticated_user(client)

    configuration = create_configuration(
        db,
        name="Student Configuration",
        interests=["AI", "engineering"],
        preferences={"theme": "dark"},
    )

    result = client.get(
        f"/api/v1/base-configurations/{configuration.id}",
        headers=headers,
    )

    assert result.status_code == 200, result.text

    data = result.json()

    assert data["id"] == str(configuration.id)
    assert data["name"] == "Student Configuration"
    assert data["interests"] == ["AI", "engineering"]
    assert data["preferences"] == {"theme": "dark"}
    assert data["created_at"]


def test_get_base_configuration_returns_404_when_not_found(
    client,
    db,
):
    clear_configurations(db)
    headers = create_authenticated_user(client)

    result = client.get(
        f"/api/v1/base-configurations/{uuid4()}",
        headers=headers,
    )

    assert result.status_code == 404
    assert result.json()["detail"] == "Base configuration not found!"


def test_list_base_configurations_requires_authentication(client):
    result = client.get("/api/v1/base-configurations")

    assert result.status_code == 401


def test_get_base_configuration_requires_authentication(client):
    result = client.get(
        f"/api/v1/base-configurations/{uuid4()}"
    )

    assert result.status_code == 401


def test_get_base_configuration_rejects_invalid_uuid(client):
    headers = create_authenticated_user(client)

    result = client.get(
        "/api/v1/base-configurations/not-a-uuid",
        headers=headers,
    )

    assert result.status_code == 422