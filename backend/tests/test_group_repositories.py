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


def test_friend_group_repository_create(db):
    repository = FriendGroupRepository(db)

    group = repository.create(
        name="MUSE Crew",
    )

    db.commit()

    saved_group = db.query(FriendGroup).filter(
        FriendGroup.id == group.id
    ).first()

    assert saved_group is not None
    assert saved_group.name == "MUSE Crew"


def test_group_membership_repository_create(db):
    user = User(
        email=f"{uuid4()}@example.com",
        password_hash="hashed-password",
        display_name="Test User",
    )

    group = FriendGroup(
        name="MUSE Crew",
    )

    db.add(user)
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