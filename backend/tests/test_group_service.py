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
from app.services.group_service import GroupService


def test_create_group_adds_creator_as_member(db):
    user = User(
        email=f"{uuid4()}@example.com",
        password_hash="hashed-password",
        display_name="Test User",
    )

    db.add(user)
    db.flush()

    group_repository = FriendGroupRepository(db)
    membership_repository = GroupMembershipRepository(db)

    service = GroupService(
        group_repository=group_repository,
        membership_repository=membership_repository,
    )

    group = service.create_group(
        user_id=user.id,
        name="MUSE Crew",
    )

    saved_group = db.query(FriendGroup).filter(
        FriendGroup.id == group.id
    ).first()

    assert saved_group is not None
    assert saved_group.name == "MUSE Crew"

    membership = db.query(GroupMembership).filter(
        GroupMembership.user_id == user.id,
        GroupMembership.group_id == group.id,
    ).first()

    assert membership is not None