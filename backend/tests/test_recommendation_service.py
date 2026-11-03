from uuid import uuid4

import pytest

from app.models.recommendation import Recommendation
from app.models.user import User
from app.services.recommendation_service import RecommendationService


def create_user(db):
    user = User(
        email=f"{uuid4()}@example.com",
        password_hash="hashed_password",
        display_name="Recommendation Tester",
    )
    db.add(user)
    db.flush()
    return user


def create_recommendation(service, user_id, **overrides):
    payload = {
        "recommendation_type": "activity",
        "title": "Visit a museum",
        "source": "system",
        "description": "Explore the local museum.",
    }
    payload.update(overrides)

    return service.create_recommendation(
        user_id=user_id,
        **payload,
    )


def test_create_recommendation(db):
    user = create_user(db)
    service = RecommendationService(db)

    recommendation = create_recommendation(service, user.id)

    assert recommendation.id is not None
    assert recommendation.user_id == user.id
    assert recommendation.recommendation_type == "activity"
    assert recommendation.title == "Visit a museum"
    assert recommendation.description == "Explore the local museum."
    assert recommendation.source == "system"


def test_create_recommendation_without_description(db):
    user = create_user(db)
    service = RecommendationService(db)

    recommendation = create_recommendation(
        service,
        user.id,
        description=None,
    )

    assert recommendation.description is None


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("recommendation_type", "", "Recommendation type"),
        ("recommendation_type", "   ", "Recommendation type"),
        ("title", "", "Title"),
        ("title", "   ", "Title"),
        ("source", "", "Source"),
        ("source", "   ", "Source"),
        ("description", "", "Description"),
        ("description", "   ", "Description"),
    ],
)
def test_create_recommendation_rejects_empty_fields(
    db,
    field,
    value,
    message,
):
    user = create_user(db)
    service = RecommendationService(db)

    with pytest.raises(ValueError, match=message):
        create_recommendation(
            service,
            user.id,
            **{field: value},
        )


def test_get_recommendation(db):
    user = create_user(db)
    service = RecommendationService(db)

    created = create_recommendation(service, user.id)

    result = service.get_recommendation(created.id, user.id)

    assert result is not None
    assert result.id == created.id


def test_get_recommendation_returns_none_for_unknown_id(db):
    user = create_user(db)
    service = RecommendationService(db)

    result = service.get_recommendation(uuid4(), user.id)

    assert result is None


def test_get_recommendation_does_not_expose_another_users_record(db):
    owner = create_user(db)
    another_user = create_user(db)
    service = RecommendationService(db)

    created = create_recommendation(service, owner.id)

    result = service.get_recommendation(
        created.id,
        another_user.id,
    )

    assert result is None


def test_get_user_recommendations(db):
    user = create_user(db)
    service = RecommendationService(db)

    create_recommendation(service, user.id, title="First")
    create_recommendation(service, user.id, title="Second")

    results = service.get_user_recommendations(user.id)

    assert len(results) == 2
    assert all(item.user_id == user.id for item in results)


def test_get_user_recommendations_returns_empty_list(db):
    user = create_user(db)
    service = RecommendationService(db)

    results = service.get_user_recommendations(user.id)

    assert results == []


def test_get_recommendations_by_type(db):
    user = create_user(db)
    service = RecommendationService(db)

    create_recommendation(
        service,
        user.id,
        recommendation_type="activity",
    )
    create_recommendation(
        service,
        user.id,
        recommendation_type="food",
    )
    create_recommendation(
        service,
        user.id,
        recommendation_type="activity",
        title="Go hiking",
    )

    results = service.get_recommendations_by_type(
        user.id,
        "activity",
    )

    assert len(results) == 2
    assert all(
        item.recommendation_type == "activity"
        for item in results
    )


def test_get_recommendations_by_type_rejects_empty_type(db):
    user = create_user(db)
    service = RecommendationService(db)

    with pytest.raises(ValueError, match="Recommendation type"):
        service.get_recommendations_by_type(user.id, "  ")


def test_get_recommendations_by_source(db):
    user = create_user(db)
    service = RecommendationService(db)

    create_recommendation(service, user.id, source="system")
    create_recommendation(
        service,
        user.id,
        source="ai",
        title="AI recommendation",
    )
    create_recommendation(
        service,
        user.id,
        source="system",
        title="Another system recommendation",
    )

    results = service.get_recommendations_by_source(
        user.id,
        "system",
    )

    assert len(results) == 2
    assert all(item.source == "system" for item in results)


def test_get_recommendations_by_source_rejects_empty_source(db):
    user = create_user(db)
    service = RecommendationService(db)

    with pytest.raises(ValueError, match="Source"):
        service.get_recommendations_by_source(user.id, "  ")


def test_delete_recommendation(db):
    user = create_user(db)
    service = RecommendationService(db)

    created = create_recommendation(service, user.id)

    result = service.delete_recommendation(created.id, user.id)

    assert result is True
    assert db.get(Recommendation, created.id) is None


def test_delete_recommendation_rejects_another_users_record(db):
    owner = create_user(db)
    another_user = create_user(db)
    service = RecommendationService(db)

    created = create_recommendation(service, owner.id)

    with pytest.raises(ValueError, match="Recommendation not found"):
        service.delete_recommendation(created.id, another_user.id)

    assert db.get(Recommendation, created.id) is not None


def test_delete_unknown_recommendation(db):
    user = create_user(db)
    service = RecommendationService(db)

    with pytest.raises(ValueError, match="Recommendation not found"):
        service.delete_recommendation(uuid4(), user.id)