from uuid import uuid4

import pytest

from app.models.friend_group import FriendGroup
from app.models.group_activity import GroupActivity
from app.models.group_membership import GroupMembership
from app.models.group_activity_response import GroupActivityResponse
from app.models.user import User
from app.services.group_activity_response_service import (
    GroupActivityResponseService,
)


def create_test_user(db):
    user = User(
        email=f"{uuid4()}@example.com",
        password_hash="test-hash",
        display_name="Response Tester",
    )
    db.add(user)
    db.flush()
    return user


def create_test_activity(db, user):
    group = FriendGroup(name=f"Group-{uuid4()}")
    db.add(group)
    db.flush()

    db.add(
        GroupMembership(
            user_id=user.id,
            group_id=group.id,
        )
    )

    activity = GroupActivity(
        group_id=group.id,
        created_by=user.id,
        activity_type="poll",
        title="Weekend plans",
        description="Choose an activity",
    )
    db.add(activity)
    db.flush()

    return group, activity


def test_create_response_successfully(db):
    user = create_test_user(db)
    _, activity = create_test_activity(db, user)
    service = GroupActivityResponseService(db)

    result = service.create_response(
        activity_id=activity.id,
        user_id=user.id,
        response="Movie night",
        note="Saturday works best",
    )

    assert result.id is not None
    assert result.activity_id == activity.id
    assert result.user_id == user.id
    assert result.response == "Movie night"
    assert result.note == "Saturday works best"


def test_create_response_rejects_missing_activity(db):
    user = create_test_user(db)
    service = GroupActivityResponseService(db)

    with pytest.raises(ValueError, match="Group activity not found"):
        service.create_response(
            activity_id=uuid4(),
            user_id=user.id,
            response="Movie night",
        )


def test_create_response_rejects_non_member(db):
    owner = create_test_user(db)
    outsider = create_test_user(db)
    _, activity = create_test_activity(db, owner)
    service = GroupActivityResponseService(db)

    with pytest.raises(ValueError, match="not a member"):
        service.create_response(
            activity_id=activity.id,
            user_id=outsider.id,
            response="Movie night",
        )


def test_create_response_rejects_duplicate_response(db):
    user = create_test_user(db)
    _, activity = create_test_activity(db, user)
    service = GroupActivityResponseService(db)

    service.create_response(
        activity_id=activity.id,
        user_id=user.id,
        response="Movie night",
    )

    with pytest.raises(ValueError, match="already responded"):
        service.create_response(
            activity_id=activity.id,
            user_id=user.id,
            response="Bowling",
        )


def test_get_response_successfully(db):
    user = create_test_user(db)
    _, activity = create_test_activity(db, user)
    service = GroupActivityResponseService(db)

    created = service.create_response(
        activity_id=activity.id,
        user_id=user.id,
        response="Hiking",
    )

    result = service.get_response(created.id, user.id)

    assert result.id == created.id
    assert result.response == "Hiking"


def test_get_response_rejects_missing_response(db):
    user = create_test_user(db)
    service = GroupActivityResponseService(db)

    with pytest.raises(
        ValueError, match="Group activity response not found"
    ):
        service.get_response(uuid4(), user.id)


def test_get_response_rejects_non_member(db):
    owner = create_test_user(db)
    outsider = create_test_user(db)
    _, activity = create_test_activity(db, owner)
    service = GroupActivityResponseService(db)

    created = service.create_response(
        activity_id=activity.id,
        user_id=owner.id,
        response="Hiking",
    )

    with pytest.raises(ValueError, match="not a member"):
        service.get_response(created.id, outsider.id)


def test_get_activity_responses_returns_responses(db):
    first_user = create_test_user(db)
    group, activity = create_test_activity(db, first_user)
    second_user = create_test_user(db)

    db.add(
        GroupMembership(
            user_id=second_user.id,
            group_id=group.id,
        )
    )
    db.flush()

    service = GroupActivityResponseService(db)

    first = service.create_response(
        activity_id=activity.id,
        user_id=first_user.id,
        response="Movie night",
    )
    second = service.create_response(
        activity_id=activity.id,
        user_id=second_user.id,
        response="Bowling",
    )

    results = service.get_activity_responses(activity.id, first_user.id)

    assert {item.id for item in results} == {first.id, second.id}


def test_get_activity_responses_rejects_non_member(db):
    owner = create_test_user(db)
    outsider = create_test_user(db)
    _, activity = create_test_activity(db, owner)
    service = GroupActivityResponseService(db)

    with pytest.raises(ValueError, match="not a member"):
        service.get_activity_responses(activity.id, outsider.id)


def test_delete_response_by_creator(db):
    user = create_test_user(db)
    _, activity = create_test_activity(db, user)
    service = GroupActivityResponseService(db)

    created = service.create_response(
        activity_id=activity.id,
        user_id=user.id,
        response="Movie night",
    )

    assert service.delete_response(created.id, user.id) is True
    assert service.response_repository.get_by_id(created.id) is None


def test_delete_response_rejects_non_creator(db):
    owner = create_test_user(db)
    other_user = create_test_user(db)
    _, activity = create_test_activity(db, owner)
    service = GroupActivityResponseService(db)

    created = service.create_response(
        activity_id=activity.id,
        user_id=owner.id,
        response="Movie night",
    )

    with pytest.raises(
        ValueError, match="Only the response creator can delete it"
    ):
        service.delete_response(created.id, other_user.id)


def test_delete_response_rejects_missing_response(db):
    user = create_test_user(db)
    service = GroupActivityResponseService(db)

    with pytest.raises(
        ValueError, match="Group activity response not found"
    ):
        service.delete_response(uuid4(), user.id)