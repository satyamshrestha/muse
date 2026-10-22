from uuid import uuid4

import pytest

from app.models.friend_group import FriendGroup
from app.models.group_activity import GroupActivity
from app.models.group_membership import GroupMembership
from app.models.user import User
from app.services.group_activity_service import GroupActivityService


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


def add_member(db, user: User, group: FriendGroup) -> None:
    db.add(GroupMembership(user_id=user.id, group_id=group.id))
    db.flush()


def test_create_activity_for_group_member(db):
    user = create_test_user(db)
    group = create_test_group(db)
    add_member(db, user, group)

    service = GroupActivityService(db)
    activity = service.create_activity(
        group_id=group.id,
        user_id=user.id,
        activity_type="poll",
        title="Weekend plans",
        description="Choose an activity",
    )

    assert activity.id is not None
    assert activity.group_id == group.id
    assert activity.created_by == user.id
    assert activity.title == "Weekend plans"


def test_create_activity_rejects_missing_group(db):
    user = create_test_user(db)
    service = GroupActivityService(db)

    with pytest.raises(ValueError, match="Group not found"):
        service.create_activity(
            group_id=uuid4(),
            user_id=user.id,
            activity_type="poll",
            title="Weekend plans",
        )


def test_create_activity_rejects_non_member(db):
    user = create_test_user(db)
    group = create_test_group(db)
    service = GroupActivityService(db)

    with pytest.raises(
        ValueError, match="not a member of this group"
    ):
        service.create_activity(
            group_id=group.id,
            user_id=user.id,
            activity_type="poll",
            title="Weekend plans",
        )


def test_get_activity_for_group_member(db):
    user = create_test_user(db)
    group = create_test_group(db)
    add_member(db, user, group)

    service = GroupActivityService(db)
    activity = service.create_activity(
        group_id=group.id,
        user_id=user.id,
        activity_type="event",
        title="Study session",
    )

    result = service.get_activity(activity.id, user.id)

    assert result.id == activity.id


def test_get_activity_rejects_non_member(db):
    creator = create_test_user(db)
    outsider = create_test_user(db)
    group = create_test_group(db)
    add_member(db, creator, group)

    service = GroupActivityService(db)
    activity = service.create_activity(
        group_id=group.id,
        user_id=creator.id,
        activity_type="poll",
        title="Movie night",
    )

    with pytest.raises(
        ValueError, match="not a member of this group"
    ):
        service.get_activity(activity.id, outsider.id)


def test_get_group_activities_returns_activities(db):
    user = create_test_user(db)
    group = create_test_group(db)
    add_member(db, user, group)

    service = GroupActivityService(db)
    first = service.create_activity(
        group.id, user.id, "poll", "Movie night"
    )
    second = service.create_activity(
        group.id, user.id, "event", "Study session"
    )

    activities = service.get_group_activities(group.id, user.id)

    assert {item.id for item in activities} == {first.id, second.id}


def test_get_group_activities_rejects_non_member(db):
    user = create_test_user(db)
    group = create_test_group(db)
    service = GroupActivityService(db)

    with pytest.raises(
        ValueError, match="not a member of this group"
    ):
        service.get_group_activities(group.id, user.id)


def test_delete_activity_by_creator(db):
    user = create_test_user(db)
    group = create_test_group(db)
    add_member(db, user, group)

    service = GroupActivityService(db)
    activity = service.create_activity(
        group.id, user.id, "poll", "Delete me"
    )

    assert service.delete_activity(activity.id, user.id) is True
    assert db.get(GroupActivity, activity.id) is None


def test_delete_activity_rejects_non_creator(db):
    creator = create_test_user(db)
    other_user = create_test_user(db)
    group = create_test_group(db)
    add_member(db, creator, group)
    add_member(db, other_user, group)

    service = GroupActivityService(db)
    activity = service.create_activity(
        group.id, creator.id, "poll", "Keep me"
    )

    with pytest.raises(
        ValueError, match="Only the activity creator can delete it"
    ):
        service.delete_activity(activity.id, other_user.id)


def test_get_activity_rejects_missing_activity(db):
    user = create_test_user(db)
    service = GroupActivityService(db)

    with pytest.raises(ValueError, match="Group activity not found"):
        service.get_activity(uuid4(), user.id)