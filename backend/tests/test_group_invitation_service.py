import hashlib
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.exceptions.group_exceptions import GroupNotFoundException
from app.models.group_invitation import GroupInvitation
from app.models.user import User
from app.repositories.friend_group_repository import FriendGroupRepository
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


def create_group_with_member(db, service, user_id):
    return service.create_group(
        user_id=user_id,
        name="Invitation Test Group",
    )


def get_invitation_by_token(db, token: str) -> GroupInvitation:
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()

    return (
        db.query(GroupInvitation)
        .filter_by(token_hash=token_hash)
        .one()
    )


def test_create_invitation_returns_token_and_stores_only_hash(db):
    user = create_test_user(db)
    db.commit()

    service = create_service(db)
    group = create_group_with_member(db, service, user.id)

    result = service.create_invitation(user.id, group.id)

    assert result["token"]
    assert result["expires_at"] is not None

    expected_hash = hashlib.sha256(
        result["token"].encode("utf-8")
    ).hexdigest()

    invitation = get_invitation_by_token(db, result["token"])

    assert invitation.token_hash == expected_hash
    assert invitation.token_hash != result["token"]
    assert invitation.group_id == group.id
    assert invitation.created_by == user.id
    assert invitation.expires_at == result["expires_at"]


def test_create_invitation_rejects_non_member(db):
    member = create_test_user(db)
    outsider = create_test_user(db)
    db.commit()

    service = create_service(db)
    group = create_group_with_member(db, service, member.id)

    invitation_count_before = db.query(GroupInvitation).count()

    with pytest.raises(GroupNotFoundException):
        service.create_invitation(outsider.id, group.id)

    assert (
        db.query(GroupInvitation).count()
        == invitation_count_before
    )


def test_create_invitation_rejects_unknown_group(db):
    user = create_test_user(db)
    db.commit()

    service = create_service(db)

    invitation_count_before = db.query(GroupInvitation).count()

    with pytest.raises(GroupNotFoundException):
        service.create_invitation(user.id, uuid4())

    assert (
        db.query(GroupInvitation).count()
        == invitation_count_before
    )


def test_create_invitation_rolls_back_when_repository_creation_fails(
    db,
    monkeypatch,
):
    user = create_test_user(db)
    db.commit()

    service = create_service(db)
    group = create_group_with_member(db, service, user.id)

    invitation_count_before = db.query(GroupInvitation).count()

    def fail_create(*args, **kwargs):
        raise RuntimeError("Simulated invitation creation failure")

    monkeypatch.setattr(
        service.invitation_repository,
        "create",
        fail_create,
    )

    with pytest.raises(
        RuntimeError,
        match="Simulated invitation creation failure",
    ):
        service.create_invitation(user.id, group.id)

    assert (
        db.query(GroupInvitation).count()
        == invitation_count_before
    )


def test_revoke_invitation_marks_valid_invitation_revoked(db):
    user = create_test_user(db)
    db.commit()

    service = create_service(db)
    group = create_group_with_member(db, service, user.id)

    result = service.create_invitation(user.id, group.id)
    invitation = get_invitation_by_token(db, result["token"])

    service.revoke_invitation(
        user_id=user.id,
        group_id=group.id,
        invitation_id=invitation.id,
    )

    db.refresh(invitation)

    assert invitation.revoked_at is not None
    assert invitation.redeemed_at is None


def test_revoke_invitation_rejects_non_member(db):
    member = create_test_user(db)
    outsider = create_test_user(db)
    db.commit()

    service = create_service(db)
    group = create_group_with_member(db, service, member.id)

    result = service.create_invitation(member.id, group.id)
    invitation = get_invitation_by_token(db, result["token"])

    with pytest.raises(GroupNotFoundException):
        service.revoke_invitation(
            user_id=outsider.id,
            group_id=group.id,
            invitation_id=invitation.id,
        )

    db.refresh(invitation)

    assert invitation.revoked_at is None


def test_revoke_invitation_rejects_unknown_invitation(db):
    user = create_test_user(db)
    db.commit()

    service = create_service(db)
    group = create_group_with_member(db, service, user.id)

    with pytest.raises(HTTPException) as exc_info:
        service.revoke_invitation(
            user_id=user.id,
            group_id=group.id,
            invitation_id=uuid4(),
        )

    assert exc_info.value.status_code == 404


@pytest.mark.parametrize(
    "invitation_state",
    ["expired", "revoked", "redeemed"],
)
def test_join_group_rejects_invalid_invitation_state(
    db,
    invitation_state,
):
    owner = create_test_user(db)
    new_member = create_test_user(db)
    db.commit()

    service = create_service(db)
    group = create_group_with_member(db, service, owner.id)

    result = service.create_invitation(owner.id, group.id)
    invitation = get_invitation_by_token(db, result["token"])

    if invitation_state == "expired":
        invitation.expires_at = (
            datetime.now(timezone.utc) - timedelta(minutes=1)
        )
    elif invitation_state == "revoked":
        invitation.revoked_at = datetime.now(timezone.utc)
    elif invitation_state == "redeemed":
        invitation.redeemed_at = datetime.now(timezone.utc)

    db.commit()

    with pytest.raises(HTTPException) as exc_info:
        service.join_group_with_invitation(
            user_id=new_member.id,
            token=result["token"],
        )

    assert exc_info.value.status_code == 404

    membership = service.membership_repository.get_membership(
        user_id=new_member.id,
        group_id=group.id,
    )

    assert membership is None


def test_join_group_rolls_back_invitation_when_membership_creation_fails(
    db,
    monkeypatch,
):
    owner = create_test_user(db)
    new_member = create_test_user(db)
    db.commit()

    service = create_service(db)
    group = create_group_with_member(db, service, owner.id)

    result = service.create_invitation(owner.id, group.id)
    invitation = get_invitation_by_token(db, result["token"])

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
        service.join_group_with_invitation(
            user_id=new_member.id,
            token=result["token"],
        )

    db.refresh(invitation)

    assert invitation.redeemed_at is None

    membership = service.membership_repository.get_membership(
        user_id=new_member.id,
        group_id=group.id,
    )

    assert membership is None