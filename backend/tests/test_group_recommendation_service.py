from uuid import uuid4

import pytest

from app.models.friend_group import FriendGroup
from app.models.group_recommendation import GroupRecommendation
from app.models.user import User
from app.services.group_recommendation_service import (
    GroupRecommendationService,
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


def create_recommendation(service, group_id, created_by, **overrides):
    data = {
        "recommendation_type": "activity",
        "title": "Go hiking",
        "description": "Explore a nearby mountain trail.",
    }
    data.update(overrides)

    return service.create_recommendation(
        group_id=group_id,
        created_by=created_by,
        **data,
    )


def test_create_group_recommendation(db):
    user = create_user(db)
    group = create_group(db)
    service = GroupRecommendationService(db)

    recommendation = create_recommendation(
        service,
        group.id,
        user.id,
    )

    assert recommendation.id is not None
    assert recommendation.group_id == group.id
    assert recommendation.created_by == user.id
    assert recommendation.recommendation_type == "activity"
    assert recommendation.title == "Go hiking"
    assert recommendation.description == "Explore a nearby mountain trail."


def test_create_recommendation_without_description(db):
    user = create_user(db)
    group = create_group(db)
    service = GroupRecommendationService(db)

    recommendation = create_recommendation(
        service,
        group.id,
        user.id,
        description=None,
    )

    assert recommendation.description is None


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("recommendation_type", "", "Recommendation type cannot be empty"),
        ("recommendation_type", "   ", "Recommendation type cannot be empty"),
        ("title", "", "Title cannot be empty"),
        ("title", "   ", "Title cannot be empty"),
        ("description", "   ", "Description cannot be empty"),
    ],
)
def test_create_recommendation_rejects_invalid_data(
    db,
    field,
    value,
    message,
):
    user = create_user(db)
    group = create_group(db)
    service = GroupRecommendationService(db)

    with pytest.raises(ValueError, match=message):
        create_recommendation(
            service,
            group.id,
            user.id,
            **{field: value},
        )


def test_get_recommendation_returns_existing_record(db):
    user = create_user(db)
    group = create_group(db)
    service = GroupRecommendationService(db)

    created = create_recommendation(service, group.id, user.id)

    result = service.get_recommendation(created.id)

    assert result is not None
    assert result.id == created.id


def test_get_recommendation_returns_none_for_unknown_id(db):
    service = GroupRecommendationService(db)

    result = service.get_recommendation(uuid4())

    assert result is None


def test_get_group_recommendations(db):
    user = create_user(db)
    group_one = create_group(db, "Group One")
    group_two = create_group(db, "Group Two")
    service = GroupRecommendationService(db)

    first = create_recommendation(
        service,
        group_one.id,
        user.id,
        title="First recommendation",
    )

    create_recommendation(
        service,
        group_two.id,
        user.id,
        title="Other group's recommendation",
    )

    second = create_recommendation(
        service,
        group_one.id,
        user.id,
        title="Second recommendation",
    )

    results = service.get_group_recommendations(group_one.id)

    assert len(results) == 2
    assert {item.id for item in results} == {
        first.id,
        second.id,
    }


def test_get_group_recommendations_returns_empty_list(db):
    group = create_group(db)
    service = GroupRecommendationService(db)

    assert service.get_group_recommendations(group.id) == []


def test_get_recommendations_by_type(db):
    user = create_user(db)
    group = create_group(db)
    service = GroupRecommendationService(db)

    first = create_recommendation(
        service,
        group.id,
        user.id,
        title="Hiking",
        recommendation_type="activity",
    )

    create_recommendation(
        service,
        group.id,
        user.id,
        title="Restaurant",
        recommendation_type="food",
    )

    second = create_recommendation(
        service,
        group.id,
        user.id,
        title="Bowling",
        recommendation_type="activity",
    )

    results = service.get_recommendations_by_type(
        group.id,
        "activity",
    )

    assert len(results) == 2
    assert {item.id for item in results} == {
        first.id,
        second.id,
    }


def test_get_recommendations_by_type_rejects_empty_type(db):
    group = create_group(db)
    service = GroupRecommendationService(db)

    with pytest.raises(
        ValueError,
        match="Recommendation type cannot be empty",
    ):
        service.get_recommendations_by_type(group.id, " ")


def test_get_recommendations_by_type_returns_empty_list(db):
    group = create_group(db)
    service = GroupRecommendationService(db)

    results = service.get_recommendations_by_type(
        group.id,
        "travel",
    )

    assert results == []


def test_delete_recommendation(db):
    user = create_user(db)
    group = create_group(db)
    service = GroupRecommendationService(db)

    recommendation = create_recommendation(
        service,
        group.id,
        user.id,
    )

    result = service.delete_recommendation(recommendation.id)

    assert result is True
    assert db.get(GroupRecommendation, recommendation.id) is None


def test_delete_unknown_recommendation_raises_error(db):
    service = GroupRecommendationService(db)

    with pytest.raises(
        ValueError,
        match="Group recommendation not found",
    ):
        service.delete_recommendation(uuid4())