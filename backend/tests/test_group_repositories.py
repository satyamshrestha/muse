
from uuid import uuid4

from app.models.friend_group import FriendGroup
from app.models.group_membership import GroupMembership
from app.models.user import User
from app.repositories.friend_group_repository import (
    FriendGroupRepository,
)
from app.repositories.group_membership_repository import (
    GroupMembershipRepository,
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


def test_friend_group_repository_create(db):
    repository = FriendGroupRepository(db)

    group = repository.create(name="MUSE Crew")
    db.commit()

    saved_group = db.query(FriendGroup).filter(
        FriendGroup.id == group.id
    ).first()

    assert saved_group is not None
    assert saved_group.name == "MUSE Crew"


def test_group_membership_repository_create(db):
    user = create_test_user(db)
    group = FriendGroup(name="MUSE Crew")
    db.add(group)
    db.flush()

    repository = GroupMembershipRepository(db)
    membership = repository.create(
        user_id=user.id,
        group_id=group.id,
    )
    db.commit()

    saved_membership = db.query(GroupMembership).filter(
        GroupMembership.user_id == user.id,
        GroupMembership.group_id == group.id,
    ).first()

    assert saved_membership is not None
    assert membership.user_id == user.id
    assert membership.group_id == group.id


def test_friend_group_repository_get_by_id(db):
    group = FriendGroup(name="MUSE Crew")
    db.add(group)
    db.flush()

    repository = FriendGroupRepository(db)
    result = repository.get_by_id(group.id)

    assert result is not None
    assert result.id == group.id
    assert result.name == "MUSE Crew"


def test_friend_group_repository_get_by_id_not_found(db):
    repository = FriendGroupRepository(db)

    assert repository.get_by_id(uuid4()) is None


def test_get_groups_for_user_returns_only_member_groups(db):
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

    repository = GroupMembershipRepository(db)
    groups = repository.get_groups_for_user(user.id)

    assert {group.id for group in groups} == {
        first_group.id,
        second_group.id,
    }
    assert other_group.id not in {group.id for group in groups}


def test_is_member_returns_true_for_existing_membership(db):
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

    repository = GroupMembershipRepository(db)

    assert repository.is_member(user.id, group.id) is True


def test_is_member_returns_false_without_membership(db):
    user = create_test_user(db)
    group = FriendGroup(name="MUSE Crew")
    db.add(group)
    db.commit()

    repository = GroupMembershipRepository(db)

    assert repository.is_member(user.id, group.id) is False

def test_get_membership_returns_existing_membership(db):
    user = create_test_user(db)
    group = FriendGroup(name="MUSE Crew")
    db.add(group)
    db.flush()

    membership = GroupMembership(
        user_id=user.id,
        group_id=group.id,
    )
    db.add(membership)
    db.flush()

    repository = GroupMembershipRepository(db)
    result = repository.get_membership(user.id, group.id)

    assert result is not None
    assert result.user_id == user.id
    assert result.group_id == group.id


def test_get_membership_returns_none_without_membership(db):
    user = create_test_user(db)
    group = FriendGroup(name="MUSE Crew")
    db.add(group)
    db.flush()

    repository = GroupMembershipRepository(db)
    result = repository.get_membership(user.id, group.id)

    assert result is None