from uuid import uuid4

from app.models.recommendation import Recommendation
from app.models.user import User
from app.repositories.recommendation_repository import (
    RecommendationRepository,
)


def create_user(db):
    user = User(
        email=f"{uuid4()}@example.com",
        password_hash="hashed_password",
        display_name="Recommendation Tester",
    )
    db.add(user)
    db.flush()
    return user


def test_create_recommendation(db):
    user = create_user(db)
    repository = RecommendationRepository(db)

    recommendation = repository.create(
        user_id=user.id,
        recommendation_type="activity",
        title="Visit a museum",
        description="Explore the local museum.",
        source="system",
    )

    assert recommendation.id is not None
    assert recommendation.user_id == user.id
    assert recommendation.recommendation_type == "activity"
    assert recommendation.title == "Visit a museum"
    assert recommendation.description == "Explore the local museum."
    assert recommendation.source == "system"


def test_create_recommendation_without_description(db):
    user = create_user(db)
    repository = RecommendationRepository(db)

    recommendation = repository.create(
        user_id=user.id,
        recommendation_type="activity",
        title="Go hiking",
        source="ai",
    )

    assert recommendation.description is None


def test_get_recommendation_by_id_for_user(db):
    user = create_user(db)
    repository = RecommendationRepository(db)

    created = repository.create(
        user_id=user.id,
        recommendation_type="activity",
        title="Visit a museum",
        source="system",
    )

    result = repository.get_by_id_for_user(created.id, user.id)

    assert result is not None
    assert result.id == created.id


def test_get_recommendation_returns_none_for_unknown_id(db):
    user = create_user(db)
    repository = RecommendationRepository(db)

    result = repository.get_by_id_for_user(uuid4(), user.id)

    assert result is None


def test_get_recommendation_does_not_expose_another_users_record(db):
    owner = create_user(db)
    another_user = create_user(db)
    repository = RecommendationRepository(db)

    created = repository.create(
        user_id=owner.id,
        recommendation_type="activity",
        title="Private recommendation",
        source="system",
    )

    result = repository.get_by_id_for_user(
        created.id,
        another_user.id,
    )

    assert result is None


def test_get_recommendations_for_user(db):
    user = create_user(db)
    repository = RecommendationRepository(db)

    repository.create(
        user_id=user.id,
        recommendation_type="activity",
        title="First recommendation",
        source="system",
    )
    repository.create(
        user_id=user.id,
        recommendation_type="food",
        title="Second recommendation",
        source="ai",
    )

    results = repository.get_for_user(user.id)

    assert len(results) == 2
    assert all(item.user_id == user.id for item in results)


def test_get_recommendations_does_not_include_another_users_records(db):
    first_user = create_user(db)
    second_user = create_user(db)
    repository = RecommendationRepository(db)

    repository.create(
        user_id=first_user.id,
        recommendation_type="activity",
        title="First user's recommendation",
        source="system",
    )
    repository.create(
        user_id=second_user.id,
        recommendation_type="activity",
        title="Second user's recommendation",
        source="system",
    )

    results = repository.get_for_user(first_user.id)

    assert len(results) == 1
    assert results[0].user_id == first_user.id


def test_get_recommendations_returns_empty_list(db):
    user = create_user(db)
    repository = RecommendationRepository(db)

    results = repository.get_for_user(user.id)

    assert results == []


def test_get_recommendations_by_type_for_user(db):
    user = create_user(db)
    repository = RecommendationRepository(db)

    repository.create(
        user_id=user.id,
        recommendation_type="activity",
        title="Visit a museum",
        source="system",
    )
    repository.create(
        user_id=user.id,
        recommendation_type="food",
        title="Try a restaurant",
        source="ai",
    )
    repository.create(
        user_id=user.id,
        recommendation_type="activity",
        title="Go hiking",
        source="ai",
    )

    results = repository.get_by_type_for_user(
        user.id,
        "activity",
    )

    assert len(results) == 2
    assert all(
        item.recommendation_type == "activity"
        for item in results
    )


def test_get_recommendations_by_type_returns_empty_list(db):
    user = create_user(db)
    repository = RecommendationRepository(db)

    results = repository.get_by_type_for_user(
        user.id,
        "nonexistent",
    )

    assert results == []


def test_get_recommendations_by_source_for_user(db):
    user = create_user(db)
    repository = RecommendationRepository(db)

    repository.create(
        user_id=user.id,
        recommendation_type="activity",
        title="First recommendation",
        source="system",
    )
    repository.create(
        user_id=user.id,
        recommendation_type="food",
        title="Second recommendation",
        source="ai",
    )
    repository.create(
        user_id=user.id,
        recommendation_type="activity",
        title="Third recommendation",
        source="system",
    )

    results = repository.get_by_source_for_user(
        user.id,
        "system",
    )

    assert len(results) == 2
    assert all(item.source == "system" for item in results)


def test_get_recommendations_by_source_returns_empty_list(db):
    user = create_user(db)
    repository = RecommendationRepository(db)

    results = repository.get_by_source_for_user(
        user.id,
        "nonexistent",
    )

    assert results == []


def test_delete_recommendation(db):
    user = create_user(db)
    repository = RecommendationRepository(db)

    created = repository.create(
        user_id=user.id,
        recommendation_type="activity",
        title="Delete me",
        source="system",
    )

    result = repository.delete(created.id)

    assert result is True
    assert db.get(Recommendation, created.id) is None


def test_delete_returns_false_for_unknown_id(db):
    repository = RecommendationRepository(db)

    result = repository.delete(uuid4())

    assert result is False