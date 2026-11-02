from uuid import uuid4

from app.models.friend_group import FriendGroup
from app.models.group_recommendation import GroupRecommendation
from app.models.user import User
from app.repositories.group_recommendation_repository import (
    GroupRecommendationRepository,
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


def create_group(db, name="Test Group"):
    group = FriendGroup(name=name)
    db.add(group)
    db.flush()
    return group


def create_recommendation(
    repository,
    group_id,
    created_by,
    **overrides,
):
    data = {
        "recommendation_type": "activity",
        "title": "Go hiking",
        "description": "Explore a nearby mountain trail.",
    }
    data.update(overrides)

    return repository.create(
        group_id=group_id,
        created_by=created_by,
        **data,
    )


def test_create_group_recommendation(db):
    user = create_user(db)
    group = create_group(db)
    repository = GroupRecommendationRepository(db)

    recommendation = create_recommendation(
        repository,
        group.id,
        user.id,
    )

    assert recommendation.id is not None
    assert recommendation.group_id == group.id
    assert recommendation.created_by == user.id
    assert recommendation.recommendation_type == "activity"
    assert recommendation.title == "Go hiking"
    assert recommendation.description == "Explore a nearby mountain trail."


def test_create_group_recommendation_without_description(db):
    user = create_user(db)
    group = create_group(db)
    repository = GroupRecommendationRepository(db)

    recommendation = create_recommendation(
        repository,
        group.id,
        user.id,
        description=None,
    )

    assert recommendation.description is None


def test_get_by_id_returns_recommendation(db):
    user = create_user(db)
    group = create_group(db)
    repository = GroupRecommendationRepository(db)

    created = create_recommendation(
        repository,
        group.id,
        user.id,
    )

    result = repository.get_by_id(created.id)

    assert result is not None
    assert result.id == created.id


def test_get_by_id_returns_none_for_missing_recommendation(db):
    repository = GroupRecommendationRepository(db)

    result = repository.get_by_id(uuid4())

    assert result is None


def test_get_for_group_returns_only_group_recommendations(db):
    user = create_user(db)
    group_one = create_group(db, "Group One")
    group_two = create_group(db, "Group Two")
    repository = GroupRecommendationRepository(db)

    first = create_recommendation(
        repository,
        group_one.id,
        user.id,
        title="First recommendation",
    )

    create_recommendation(
        repository,
        group_two.id,
        user.id,
        title="Other group's recommendation",
    )

    second = create_recommendation(
        repository,
        group_one.id,
        user.id,
        title="Second recommendation",
    )

    results = repository.get_for_group(group_one.id)

    assert len(results) == 2
    assert {item.id for item in results} == {
        first.id,
        second.id,
    }


def test_get_for_group_returns_empty_list_when_no_matches(db):
    group = create_group(db)
    repository = GroupRecommendationRepository(db)

    results = repository.get_for_group(group.id)

    assert results == []


def test_get_by_type_returns_matching_group_recommendations(db):
    user = create_user(db)
    group = create_group(db)
    other_group = create_group(db, "Other Group")
    repository = GroupRecommendationRepository(db)

    first = create_recommendation(
        repository,
        group.id,
        user.id,
        title="Hiking",
        recommendation_type="activity",
    )

    create_recommendation(
        repository,
        group.id,
        user.id,
        title="Restaurant",
        recommendation_type="food",
    )

    create_recommendation(
        repository,
        other_group.id,
        user.id,
        title="Other group's activity",
        recommendation_type="activity",
    )

    second = create_recommendation(
        repository,
        group.id,
        user.id,
        title="Bowling",
        recommendation_type="activity",
    )

    results = repository.get_by_type(group.id, "activity")

    assert len(results) == 2
    assert {item.id for item in results} == {
        first.id,
        second.id,
    }


def test_get_by_type_returns_empty_list_when_no_matches(db):
    user = create_user(db)
    group = create_group(db)
    repository = GroupRecommendationRepository(db)

    create_recommendation(
        repository,
        group.id,
        user.id,
        recommendation_type="food",
    )

    results = repository.get_by_type(group.id, "travel")

    assert results == []


def test_delete_group_recommendation(db):
    user = create_user(db)
    group = create_group(db)
    repository = GroupRecommendationRepository(db)

    recommendation = create_recommendation(
        repository,
        group.id,
        user.id,
    )

    result = repository.delete(recommendation.id)

    assert result is True
    assert repository.get_by_id(recommendation.id) is None


def test_delete_returns_false_for_missing_recommendation(db):
    repository = GroupRecommendationRepository(db)

    result = repository.delete(uuid4())

    assert result is False