from uuid import uuid4

from app.models.recommendation import Recommendation
from app.models.user import User
from app.repositories.recommendation_interaction_repository import (
    RecommendationInteractionRepository,
)


def create_user(db):
    user = User(
        email=f"{uuid4()}@example.com",
        password_hash="hashed_password",
        display_name="Interaction Tester",
    )
    db.add(user)
    db.flush()
    return user


def create_recommendation(db, user_id):
    recommendation = Recommendation(
        user_id=user_id,
        recommendation_type="activity",
        title="Try photography",
        description="Explore photography",
        source="ai",
    )
    db.add(recommendation)
    db.flush()
    return recommendation


def create_interaction(
    db,
    user_id,
    recommendation_id,
    interaction_type="liked",
):
    repository = RecommendationInteractionRepository(db)
    return repository.create(
        user_id=user_id,
        recommendation_id=recommendation_id,
        interaction_type=interaction_type,
    )


def test_create_interaction(db):
    user = create_user(db)
    recommendation = create_recommendation(db, user.id)

    repository = RecommendationInteractionRepository(db)

    interaction = repository.create(
        user_id=user.id,
        recommendation_id=recommendation.id,
        interaction_type="liked",
    )

    assert interaction.id is not None
    assert interaction.user_id == user.id
    assert interaction.recommendation_id == recommendation.id
    assert interaction.interaction_type == "liked"
    assert interaction.created_at is not None


def test_get_interaction_by_id(db):
    user = create_user(db)
    recommendation = create_recommendation(db, user.id)
    interaction = create_interaction(db, user.id, recommendation.id)

    repository = RecommendationInteractionRepository(db)

    result = repository.get_by_id_for_user(
        interaction_id=interaction.id,
        user_id=user.id,
    )

    assert result is not None
    assert result.id == interaction.id


def test_get_interaction_returns_none_for_unknown_id(db):
    user = create_user(db)
    repository = RecommendationInteractionRepository(db)

    result = repository.get_by_id_for_user(
        interaction_id=uuid4(),
        user_id=user.id,
    )

    assert result is None


def test_get_interaction_rejects_another_users_record(db):
    owner = create_user(db)
    another_user = create_user(db)
    recommendation = create_recommendation(db, owner.id)

    interaction = create_interaction(
        db,
        owner.id,
        recommendation.id,
    )

    repository = RecommendationInteractionRepository(db)

    result = repository.get_by_id_for_user(
        interaction_id=interaction.id,
        user_id=another_user.id,
    )

    assert result is None


def test_get_interactions_for_user(db):
    user = create_user(db)
    recommendation = create_recommendation(db, user.id)

    create_interaction(db, user.id, recommendation.id, "liked")
    create_interaction(db, user.id, recommendation.id, "saved")

    repository = RecommendationInteractionRepository(db)

    results = repository.get_for_user(user.id)

    assert len(results) == 2


def test_get_interactions_returns_empty_list_for_user_without_interactions(db):
    user = create_user(db)
    repository = RecommendationInteractionRepository(db)

    results = repository.get_for_user(user.id)

    assert results == []


def test_get_interactions_only_returns_current_users_records(db):
    user_one = create_user(db)
    user_two = create_user(db)

    recommendation_one = create_recommendation(db, user_one.id)
    recommendation_two = create_recommendation(db, user_two.id)

    create_interaction(db, user_one.id, recommendation_one.id)
    create_interaction(db, user_two.id, recommendation_two.id)

    repository = RecommendationInteractionRepository(db)

    results = repository.get_for_user(user_one.id)

    assert len(results) == 1
    assert results[0].user_id == user_one.id


def test_get_interactions_for_recommendation(db):
    user = create_user(db)
    recommendation_one = create_recommendation(db, user.id)
    recommendation_two = create_recommendation(db, user.id)

    create_interaction(db, user.id, recommendation_one.id, "liked")
    create_interaction(db, user.id, recommendation_one.id, "saved")
    create_interaction(db, user.id, recommendation_two.id, "dismissed")

    repository = RecommendationInteractionRepository(db)

    results = repository.get_for_recommendation(
        user_id=user.id,
        recommendation_id=recommendation_one.id,
    )

    assert len(results) == 2
    assert all(
        item.recommendation_id == recommendation_one.id
        for item in results
    )


def test_get_interactions_for_recommendation_returns_empty_list(db):
    user = create_user(db)
    recommendation = create_recommendation(db, user.id)

    repository = RecommendationInteractionRepository(db)

    results = repository.get_for_recommendation(
        user_id=user.id,
        recommendation_id=recommendation.id,
    )

    assert results == []


def test_get_interactions_by_type(db):
    user = create_user(db)
    recommendation = create_recommendation(db, user.id)

    create_interaction(db, user.id, recommendation.id, "liked")
    create_interaction(db, user.id, recommendation.id, "saved")
    create_interaction(db, user.id, recommendation.id, "liked")

    repository = RecommendationInteractionRepository(db)

    results = repository.get_by_type_for_user(
        user_id=user.id,
        interaction_type="liked",
    )

    assert len(results) == 2
    assert all(item.interaction_type == "liked" for item in results)


def test_get_interactions_by_type_returns_empty_list(db):
    user = create_user(db)
    recommendation = create_recommendation(db, user.id)

    create_interaction(db, user.id, recommendation.id, "liked")

    repository = RecommendationInteractionRepository(db)

    results = repository.get_by_type_for_user(
        user_id=user.id,
        interaction_type="dismissed",
    )

    assert results == []


def test_delete_interaction(db):
    user = create_user(db)
    recommendation = create_recommendation(db, user.id)
    interaction = create_interaction(db, user.id, recommendation.id)

    repository = RecommendationInteractionRepository(db)

    result = repository.delete(
        interaction_id=interaction.id,
        user_id=user.id,
    )

    assert result is True
    assert repository.get_by_id_for_user(interaction.id, user.id) is None


def test_delete_unknown_interaction_returns_false(db):
    user = create_user(db)
    repository = RecommendationInteractionRepository(db)

    result = repository.delete(
        interaction_id=uuid4(),
        user_id=user.id,
    )

    assert result is False


def test_delete_rejects_another_users_interaction(db):
    owner = create_user(db)
    another_user = create_user(db)
    recommendation = create_recommendation(db, owner.id)

    interaction = create_interaction(
        db,
        owner.id,
        recommendation.id,
    )

    repository = RecommendationInteractionRepository(db)

    result = repository.delete(
        interaction_id=interaction.id,
        user_id=another_user.id,
    )

    assert result is False
    assert repository.get_by_id_for_user(
        interaction.id,
        owner.id,
    ) is not None