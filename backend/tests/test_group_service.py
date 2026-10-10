from uuid import uuid4

import pytest

from app.exceptions.group_exceptions import (
    AlreadyGroupMemberException,
    GroupNotFoundException,
)
from app.models.friend_group import FriendGroup
from app.models.group_membership import GroupMembership
from app.models.user import User
from app.repositories.friend_group_repository import (
    FriendGroupRepository,
)
from app.repositories.group_membership_repository import (
    GroupMembershipRepository,
)
from app.services.group_service import GroupService


def create_test_user(db) -> User:
    user = User(
        email=f"{uuid4()}@example.com",
        password_hash="hashed-password",
        display_name="Test User",
    )
    db.add(user)
    db.flush()
    return user


def create_service(db) -> GroupService:
    return GroupService(
        group_repository=FriendGroupRepository(db),
        membership_repository=GroupMembershipRepository(db),
    )


def test_get_user_groups_returns_only_member_groups(db):
    user = create_test_user(db)

    first_group = FriendGroup(name="First Group")
    second_group = FriendGroup(name="Second Group")
    other_group = FriendGroup(name="Other Group")

    db.add_all([first_group, second_group, other_group])
    db.flush()

    db.add_all([
        GroupMembership(
            user_id=user.id,
            group_id=first_group.id,
        ),
        GroupMembership(
            user_id=user.id,
            group_id=second_group.id,
        ),
    ])
    db.commit()

    service = create_service(db)

    groups = service.get_user_groups(user.id)

    assert {group.id for group in groups} == {
        first_group.id,
        second_group.id,
    }
    assert other_group.id not in {group.id for group in groups}


def test_get_group_returns_group_for_member(db):
    user = create_test_user(db)
    group = FriendGroup(name="MUSE Crew")
    db.add(group)
    db.flush()

    db.add(
        GroupMembership(
            user_id=user.id,
            group_id=group.id,
        )
    )
    db.commit()

    service = create_service(db)

    result = service.get_group(user.id, group.id)

    assert result.id == group.id
    assert result.name == "MUSE Crew"


def test_get_group_rejects_non_member(db):
    user = create_test_user(db)
    group = FriendGroup(name="Private Group")
    db.add(group)
    db.commit()

    service = create_service(db)

    with pytest.raises(GroupNotFoundException):
        service.get_group(user.id, group.id)


def test_get_group_rejects_unknown_group(db):
    user = create_test_user(db)
    db.commit()

    service = create_service(db)

    with pytest.raises(GroupNotFoundException):
        service.get_group(user.id, uuid4())


def test_join_group_creates_membership(db):
    user = create_test_user(db)
    group = FriendGroup(name="MUSE Crew")
    db.add(group)
    db.commit()

    service = create_service(db)

    result = service.join_group(user.id, group.id)

    assert result.id == group.id
    assert result.name == "MUSE Crew"

    membership = service.membership_repository.get_membership(
        user_id=user.id,
        group_id=group.id,
    )
    assert membership is not None


def test_join_group_rejects_unknown_group(db):
    user = create_test_user(db)
    db.commit()

    service = create_service(db)

    with pytest.raises(GroupNotFoundException):
        service.join_group(user.id, uuid4())


def test_join_group_rejects_existing_membership(db):
    user = create_test_user(db)
    group = FriendGroup(name="MUSE Crew")
    db.add(group)
    db.flush()

    db.add(
        GroupMembership(
            user_id=user.id,
            group_id=group.id,
        )
    )
    db.commit()

    service = create_service(db)

    with pytest.raises(AlreadyGroupMemberException):
        service.join_group(user.id, group.id)

    memberships = (
        service.membership_repository.get_groups_for_user(user.id)
    )
    assert sum(
        existing_group.id == group.id
        for existing_group in memberships
    ) == 1