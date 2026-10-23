from uuid import uuid4

from app.models.friend_group import FriendGroup
from app.models.group_activity import GroupActivity
from app.models.group_activity_response import GroupActivityResponse
from app.models.user import User
from app.repositories.group_activity_response_repository import (
    GroupActivityResponseRepository,
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

    activity = GroupActivity(
        group_id=group.id,
        created_by=user.id,
        activity_type="poll",
        title="Weekend plans",
        description="Choose an activity",
    )
    db.add(activity)
    db.flush()
    return activity


def test_create_response(db):
    user = create_test_user(db)
    activity = create_test_activity(db, user)
    repository = GroupActivityResponseRepository(db)

    result = repository.create(
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
    assert result.created_at is not None


def test_create_response_without_note(db):
    user = create_test_user(db)
    activity = create_test_activity(db, user)
    repository = GroupActivityResponseRepository(db)

    result = repository.create(
        activity_id=activity.id,
        user_id=user.id,
        response="Bowling",
    )

    assert result.response == "Bowling"
    assert result.note is None


def test_get_by_id_returns_response(db):
    user = create_test_user(db)
    activity = create_test_activity(db, user)
    repository = GroupActivityResponseRepository(db)

    created = repository.create(
        activity_id=activity.id,
        user_id=user.id,
        response="Hiking",
    )

    result = repository.get_by_id(created.id)

    assert result is not None
    assert result.id == created.id
    assert result.response == "Hiking"


def test_get_by_id_returns_none_when_missing(db):
    repository = GroupActivityResponseRepository(db)

    assert repository.get_by_id(uuid4()) is None


def test_get_for_activity_returns_only_matching_responses(db):
    user = create_test_user(db)
    activity = create_test_activity(db, user)
    another_activity = create_test_activity(db, user)
    repository = GroupActivityResponseRepository(db)

    first = repository.create(
        activity_id=activity.id,
        user_id=user.id,
        response="Movie night",
    )
    second = repository.create(
        activity_id=activity.id,
        user_id=user.id,
        response="Bowling",
    )
    repository.create(
        activity_id=another_activity.id,
        user_id=user.id,
        response="Hiking",
    )

    results = repository.get_for_activity(activity.id)

    assert len(results) == 2
    assert {item.id for item in results} == {first.id, second.id}


def test_get_for_activity_returns_empty_list(db):
    user = create_test_user(db)
    activity = create_test_activity(db, user)
    repository = GroupActivityResponseRepository(db)

    assert repository.get_for_activity(activity.id) == []


def test_get_for_user_and_activity_returns_matching_response(db):
    user = create_test_user(db)
    activity = create_test_activity(db, user)
    repository = GroupActivityResponseRepository(db)

    created = repository.create(
        activity_id=activity.id,
        user_id=user.id,
        response="Movie night",
    )

    result = repository.get_for_user_and_activity(
        user_id=user.id,
        activity_id=activity.id,
    )

    assert result is not None
    assert result.id == created.id


def test_get_for_user_and_activity_returns_none_when_missing(db):
    user = create_test_user(db)
    activity = create_test_activity(db, user)
    repository = GroupActivityResponseRepository(db)

    assert (
        repository.get_for_user_and_activity(
            user_id=user.id,
            activity_id=activity.id,
        )
        is None
    )


def test_delete_response_returns_true(db):
    user = create_test_user(db)
    activity = create_test_activity(db, user)
    repository = GroupActivityResponseRepository(db)

    created = repository.create(
        activity_id=activity.id,
        user_id=user.id,
        response="Movie night",
    )

    assert repository.delete(created.id) is True
    assert repository.get_by_id(created.id) is None


def test_delete_missing_response_returns_false(db):
    repository = GroupActivityResponseRepository(db)

    assert repository.delete(uuid4()) is False