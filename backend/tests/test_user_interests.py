from uuid import uuid4

from app.auth.jwt import get_current_user_id
from app.models.user import User
from app.services.dependencies import get_user_interest_service
from app.services.user_interest_service import UserInterestService


def test_user_interest_api(db, client):
    user = User(
        email=f"{uuid4().hex}@example.com",
        password_hash="test-hash",
        display_name="Interest API Test",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    client.app.dependency_overrides[get_current_user_id] = (
        lambda: user.id
    )
    client.app.dependency_overrides[get_user_interest_service] = (
        lambda: UserInterestService(db)
    )

    try:
        response = client.put(
            "/api/v1/interests",
            json={
                "interests": [
                    "Programming",
                    "Music",
                    "programming",
                ]
            },
        )
        assert response.status_code == 200
        assert [
            item["interest"]
            for item in response.json()["interests"]
        ] == ["Programming", "Music"]

        get_response = client.get("/api/v1/interests")
        assert get_response.status_code == 200
        assert {
            item["interest"]
            for item in get_response.json()["interests"]
        } == {"Programming", "Music"}

        invalid_response = client.put(
            "/api/v1/interests",
            json={"interests": ["", "Travel"]},
        )
        assert invalid_response.status_code == 422

        empty_response = client.put(
            "/api/v1/interests",
            json={"interests": []},
        )
        assert empty_response.status_code == 200
        assert empty_response.json()["interests"] == []

    finally:
        client.app.dependency_overrides.pop(
            get_current_user_id, None
        )
        client.app.dependency_overrides.pop(
            get_user_interest_service, None
        )