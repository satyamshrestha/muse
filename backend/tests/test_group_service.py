from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.exceptions.group_exceptions import (
    AlreadyGroupMemberException,
    GroupNotFoundException,
)
from app.models.friend_group import FriendGroup
from app.models.group_invitation import GroupInvitation
from app.models.group_membership import GroupMembership
from app.models.user import User
from app.repositories.friend_group_repository import (
    FriendGroupRepository,
)
from app.repositories.group_invitation_repository import (
    GroupInvitationRepository,
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
        invitation_repository=GroupInvitationRepository(db),
    )


def add_member(db, user_id, group_id) -> None:
    db.add(
        GroupMembership(
            user_id=user_id,
            group_id=group_id,
        )
    )
    db.commit()


def test_create_group_rolls_back_when_membership_creation_fails(
    db,
    monkeypatch,
):
    user = create_test_user(db)
    db.commit()

    service = create_service(db)
    group_name = "Rollback Test Group"

    def fail_membership_creation(*args, **kwargs):
        raise RuntimeError("Simulated membership creation failure")

    monkeypatch.setattr(
        service.membership_repository,
        "create",
        fail_membership_creation,
    )

    with pytest.raises(
        RuntimeError,
        match="Simulated membership creation failure",
    ):
        service.create_group(user_id=user.id, name=group_name)

    remaining_group = (
        db.query(FriendGroup)
        .filter_by(name=group_name)
        .first()
    )

    assert remaining_group is None


def test_get_user_groups_returns_only_member_groups(db):
    user = create_test_user(db)

    first_group = FriendGroup(name="First Group")
    second_group = FriendGroup(name="Second Group")
    other_group = FriendGroup(name="Other Group")

    db.add_all([first_group, second_group, other_group])
    db.flush()

    db.add_all(
        [
            GroupMembership(
                user_id=user.id,
                group_id=first_group.id,
            ),
            GroupMembership(
                user_id=user.id,
                group_id=second_group.id,
            ),
        ]
    )
    db.commit()

    service = create_service(db)
    groups = service.get_user_groups(user.id)

    group_ids = {group.id for group in groups}

    assert group_ids == {first_group.id, second_group.id}
    assert other_group.id not in group_ids


def test_get_group_returns_group_for_member(db):
    user = create_test_user(db)
    group = FriendGroup(name="MUSE Crew")
    db.add(group)
    db.flush()

    add_member(db, user.id, group.id)

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


def test_join_group_with_invitation_creates_membership(db):
    owner = create_test_user(db)
    new_member = create_test_user(db)
    group = FriendGroup(name="MUSE Crew")
    db.add(group)
    db.flush()

    add_member(db, owner.id, group.id)

    service = create_service(db)
    invitation = service.create_invitation(owner.id, group.id)

    result = service.join_group_with_invitation(
        user_id=new_member.id,
        token=invitation["token"],
    )

    assert result.id == group.id
    assert result.name == "MUSE Crew"

    membership = service.membership_repository.get_membership(
        user_id=new_member.id,
        group_id=group.id,
    )

    assert membership is not None


def test_join_group_with_invalid_invitation_is_rejected(db):
    user = create_test_user(db)
    db.commit()

    service = create_service(db)

    with pytest.raises(HTTPException) as exc_info:
        service.join_group_with_invitation(
            user_id=user.id,
            token="invalid-invitation-token",
        )

    assert exc_info.value.status_code == 404


def test_join_group_with_invitation_rejects_existing_membership(db):
    owner = create_test_user(db)
    existing_member = create_test_user(db)
    group = FriendGroup(name="MUSE Crew")
    db.add(group)
    db.flush()

    db.add_all(
        [
            GroupMembership(
                user_id=owner.id,
                group_id=group.id,
            ),
            GroupMembership(
                user_id=existing_member.id,
                group_id=group.id,
            ),
        ]
    )
    db.commit()

    service = create_service(db)
    invitation = service.create_invitation(owner.id, group.id)

    with pytest.raises(AlreadyGroupMemberException):
        service.join_group_with_invitation(
            user_id=existing_member.id,
            token=invitation["token"],
        )

    memberships = service.membership_repository.get_groups_for_user(
        existing_member.id
    )

    assert sum(
        existing_group.id == group.id
        for existing_group in memberships
    ) == 1

    redeemed_invitation = (
        db.query(GroupInvitation)
        .filter_by(group_id=group.id)
        .one()
    )

    assert redeemed_invitation.redeemed_at is None