from uuid import uuid4

import pytest

from app.models.recommendation import Recommendation
from app.models.user import User
from app.services.recommendation_interaction_service import (
    RecommendationInteractionService,
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
    service = RecommendationInteractionService(db)
    return service.create_interaction(
        user_id=user_id,
        recommendation_id=recommendation_id,
        interaction_type=interaction_type,
    )


def test_create_interaction(db):
    user = create_user(db)
    recommendation = create_recommendation(db, user.id)

    service = RecommendationInteractionService(db)

    interaction = service.create_interaction(
        user_id=user.id,
        recommendation_id=recommendation.id,
        interaction_type="liked",
    )

    assert interaction.id is not None
    assert interaction.user_id == user.id
    assert interaction.recommendation_id == recommendation.id
    assert interaction.interaction_type == "liked"
    assert interaction.created_at is not None


def test_create_interaction_rejects_empty_type(db):
    user = create_user(db)
    recommendation = create_recommendation(db, user.id)
    service = RecommendationInteractionService(db)

    with pytest.raises(ValueError, match="Interaction type cannot be empty"):
        service.create_interaction(
            user.id,
            recommendation.id,
            "",
        )


@pytest.mark.parametrize("interaction_type", [" ", "   ", "\t", "\n"])
def test_create_interaction_rejects_whitespace_type(
    db,
    interaction_type,
):
    user = create_user(db)
    recommendation = create_recommendation(db, user.id)
    service = RecommendationInteractionService(db)

    with pytest.raises(ValueError, match="Interaction type cannot be empty"):
        service.create_interaction(
            user.id,
            recommendation.id,
            interaction_type,
        )


def test_create_interaction_rejects_unknown_recommendation(db):
    user = create_user(db)
    service = RecommendationInteractionService(db)

    with pytest.raises(ValueError, match="Recommendation not found"):
        service.create_interaction(
            user_id=user.id,
            recommendation_id=uuid4(),
            interaction_type="liked",
        )


def test_create_interaction_rejects_another_users_recommendation(db):
    owner = create_user(db)
    another_user = create_user(db)
    recommendation = create_recommendation(db, owner.id)

    service = RecommendationInteractionService(db)

    with pytest.raises(ValueError, match="Recommendation not found"):
        service.create_interaction(
            user_id=another_user.id,
            recommendation_id=recommendation.id,
            interaction_type="liked",
        )


def test_get_interaction(db):
    user = create_user(db)
    recommendation = create_recommendation(db, user.id)
    interaction = create_interaction(db, user.id, recommendation.id)

    service = RecommendationInteractionService(db)

    result = service.get_interaction(
        interaction_id=interaction.id,
        user_id=user.id,
    )

    assert result is not None
    assert result.id == interaction.id


def test_get_interaction_returns_none_for_unknown_id(db):
    user = create_user(db)
    service = RecommendationInteractionService(db)

    result = service.get_interaction(
        interaction_id=uuid4(),
        user_id=user.id,
    )

    assert result is None


def test_get_interaction_rejects_another_users_record(db):
    owner = create_user(db)
    another_user = create_user(db)
    recommendation = create_recommendation(db, owner.id)
    interaction = create_interaction(db, owner.id, recommendation.id)

    service = RecommendationInteractionService(db)

    result = service.get_interaction(
        interaction_id=interaction.id,
        user_id=another_user.id,
    )

    assert result is None


def test_get_user_interactions(db):
    user = create_user(db)
    recommendation = create_recommendation(db, user.id)

    create_interaction(db, user.id, recommendation.id, "liked")
    create_interaction(db, user.id, recommendation.id, "saved")

    service = RecommendationInteractionService(db)

    results = service.get_user_interactions(user.id)

    assert len(results) == 2


def test_get_user_interactions_returns_empty_list(db):
    user = create_user(db)
    service = RecommendationInteractionService(db)

    results = service.get_user_interactions(user.id)

    assert results == []


def test_get_recommendation_interactions(db):
    user = create_user(db)
    recommendation = create_recommendation(db, user.id)
    another_recommendation = create_recommendation(db, user.id)

    create_interaction(db, user.id, recommendation.id, "liked")
    create_interaction(db, user.id, recommendation.id, "saved")
    create_interaction(db, user.id, another_recommendation.id, "dismissed")

    service = RecommendationInteractionService(db)

    results = service.get_recommendation_interactions(
        user_id=user.id,
        recommendation_id=recommendation.id,
    )

    assert len(results) == 2
    assert all(
        item.recommendation_id == recommendation.id
        for item in results
    )


def test_get_recommendation_interactions_rejects_unknown_recommendation(db):
    user = create_user(db)
    service = RecommendationInteractionService(db)

    with pytest.raises(ValueError, match="Recommendation not found"):
        service.get_recommendation_interactions(
            user_id=user.id,
            recommendation_id=uuid4(),
        )


def test_get_recommendation_interactions_rejects_another_users_recommendation(db):
    owner = create_user(db)
    another_user = create_user(db)
    recommendation = create_recommendation(db, owner.id)

    service = RecommendationInteractionService(db)

    with pytest.raises(ValueError, match="Recommendation not found"):
        service.get_recommendation_interactions(
            user_id=another_user.id,
            recommendation_id=recommendation.id,
        )


def test_get_interactions_by_type(db):
    user = create_user(db)
    recommendation = create_recommendation(db, user.id)

    create_interaction(db, user.id, recommendation.id, "liked")
    create_interaction(db, user.id, recommendation.id, "saved")
    create_interaction(db, user.id, recommendation.id, "liked")

    service = RecommendationInteractionService(db)

    results = service.get_interactions_by_type(
        user_id=user.id,
        interaction_type="liked",
    )

    assert len(results) == 2
    assert all(item.interaction_type == "liked" for item in results)


def test_get_interactions_by_type_returns_empty_list(db):
    user = create_user(db)
    recommendation = create_recommendation(db, user.id)
    create_interaction(db, user.id, recommendation.id, "liked")

    service = RecommendationInteractionService(db)

    results = service.get_interactions_by_type(
        user_id=user.id,
        interaction_type="dismissed",
    )

    assert results == []


@pytest.mark.parametrize("interaction_type", ["", " ", "   ", "\t"])
def test_get_interactions_by_type_rejects_empty_type(
    db,
    interaction_type,
):
    user = create_user(db)
    service = RecommendationInteractionService(db)

    with pytest.raises(ValueError, match="Interaction type cannot be empty"):
        service.get_interactions_by_type(
            user_id=user.id,
            interaction_type=interaction_type,
        )


def test_delete_interaction(db):
    user = create_user(db)
    recommendation = create_recommendation(db, user.id)
    interaction = create_interaction(db, user.id, recommendation.id)

    service = RecommendationInteractionService(db)

    result = service.delete_interaction(
        interaction_id=interaction.id,
        user_id=user.id,
    )

    assert result is True
    assert service.get_interaction(interaction.id, user.id) is None


def test_delete_interaction_rejects_unknown_id(db):
    user = create_user(db)
    service = RecommendationInteractionService(db)

    with pytest.raises(ValueError, match="Interaction not found"):
        service.delete_interaction(
            interaction_id=uuid4(),
            user_id=user.id,
        )


def test_delete_interaction_rejects_another_users_record(db):
    owner = create_user(db)
    another_user = create_user(db)
    recommendation = create_recommendation(db, owner.id)
    interaction = create_interaction(db, owner.id, recommendation.id)

    service = RecommendationInteractionService(db)

    with pytest.raises(ValueError, match="Interaction not found"):
        service.delete_interaction(
            interaction_id=interaction.id,
            user_id=another_user.id,
        )

    assert service.get_interaction(interaction.id, owner.id) is not None