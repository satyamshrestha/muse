from uuid import uuid4

from app.models.friend_group import FriendGroup
from app.models.group_activity import GroupActivity
from app.models.user import User
from app.repositories.group_activity_repository import (
    GroupActivityRepository,
)


def create_test_user(db) -> User:
    user = User(
        email=f"{uuid4()}@example.com",
        password_hash="hashed-password",
        display_name="Test User",
    )
    db.add(user)
    db.flush()
    return user


def create_test_group(db) -> FriendGroup:
    group = FriendGroup(name="MUSE Crew")
    db.add(group)
    db.flush()
    return group


def test_create_group_activity(db):
    user = create_test_user(db)
    group = create_test_group(db)

    repository = GroupActivityRepository(db)
    activity = repository.create(
        group_id=group.id,
        created_by=user.id,
        activity_type="poll",
        title="Weekend plans",
        description="Choose an activity",
    )
    db.commit()

    saved = db.get(GroupActivity, activity.id)

    assert saved is not None
    assert saved.group_id == group.id
    assert saved.created_by == user.id
    assert saved.activity_type == "poll"
    assert saved.title == "Weekend plans"
    assert saved.description == "Choose an activity"


def test_create_group_activity_without_description(db):
    user = create_test_user(db)
    group = create_test_group(db)

    repository = GroupActivityRepository(db)
    activity = repository.create(
        group_id=group.id,
        created_by=user.id,
        activity_type="event",
        title="Study session",
    )

    assert activity.description is None


def test_get_by_id_returns_activity(db):
    user = create_test_user(db)
    group = create_test_group(db)
    activity = GroupActivity(
        group_id=group.id,
        created_by=user.id,
        activity_type="poll",
        title="Movie night",
    )
    db.add(activity)
    db.flush()

    repository = GroupActivityRepository(db)
    result = repository.get_by_id(activity.id)

    assert result is not None
    assert result.id == activity.id
    assert result.title == "Movie night"


def test_get_by_id_returns_none_when_missing(db):
    repository = GroupActivityRepository(db)

    assert repository.get_by_id(uuid4()) is None


def test_get_for_group_returns_only_activities_for_that_group(db):
    user = create_test_user(db)
    first_group = create_test_group(db)
    second_group = FriendGroup(name="Other Group")
    db.add(second_group)
    db.flush()

    first = GroupActivity(
        group_id=first_group.id,
        created_by=user.id,
        activity_type="poll",
        title="First activity",
    )
    second = GroupActivity(
        group_id=first_group.id,
        created_by=user.id,
        activity_type="event",
        title="Second activity",
    )
    unrelated = GroupActivity(
        group_id=second_group.id,
        created_by=user.id,
        activity_type="poll",
        title="Unrelated activity",
    )
    db.add_all([first, second, unrelated])
    db.commit()

    repository = GroupActivityRepository(db)
    activities = repository.get_for_group(first_group.id)

    assert {activity.id for activity in activities} == {
        first.id,
        second.id,
    }
    assert unrelated.id not in {activity.id for activity in activities}


def test_get_for_group_returns_empty_list_when_no_activities(db):
    group = create_test_group(db)
    repository = GroupActivityRepository(db)

    assert repository.get_for_group(group.id) == []


def test_delete_removes_activity(db):
    user = create_test_user(db)
    group = create_test_group(db)
    activity = GroupActivity(
        group_id=group.id,
        created_by=user.id,
        activity_type="poll",
        title="Delete me",
    )
    db.add(activity)
    db.commit()
    activity_id = activity.id

    repository = GroupActivityRepository(db)
    deleted = repository.delete(activity_id)
    db.commit()

    assert deleted is True
    assert repository.get_by_id(activity_id) is None


def test_delete_returns_false_when_activity_missing(db):
    repository = GroupActivityRepository(db)

    assert repository.delete(uuid4()) is False