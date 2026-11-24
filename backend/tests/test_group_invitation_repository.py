from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.models.friend_group import FriendGroup
from app.models.group_invitation import GroupInvitation
from app.models.user import User
from app.repositories.group_invitation_repository import (
    GroupInvitationRepository,
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
    group = FriendGroup(name="Invitation Test Group")
    db.add(group)
    db.flush()
    return group


def create_test_invitation(
    db,
    group: FriendGroup,
    user: User,
    *,
    token_hash: str | None = None,
    expires_at: datetime | None = None,
) -> GroupInvitation:
    repository = GroupInvitationRepository(db)

    return repository.create(
        group_id=group.id,
        created_by=user.id,
        token_hash=token_hash or uuid4().hex,
        expires_at=expires_at
        or datetime.now(timezone.utc) + timedelta(hours=1),
    )


def test_create_invitation_persists_fields(db):
    user = create_test_user(db)
    group = create_test_group(db)
    token_hash = uuid4().hex
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

    repository = GroupInvitationRepository(db)
    invitation = repository.create(
        group_id=group.id,
        created_by=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
    )

    assert invitation.id is not None
    assert invitation.group_id == group.id
    assert invitation.created_by == user.id
    assert invitation.token_hash == token_hash
    assert invitation.expires_at == expires_at
    assert invitation.redeemed_at is None
    assert invitation.revoked_at is None
    assert invitation.created_at is not None

    persisted = db.get(GroupInvitation, invitation.id)
    assert persisted is not None
    assert persisted.token_hash == token_hash


def test_redeem_if_valid_marks_invitation_redeemed(db):
    user = create_test_user(db)
    group = create_test_group(db)
    invitation = create_test_invitation(db, group, user)

    repository = GroupInvitationRepository(db)
    redeemed = repository.redeem_if_valid(invitation.token_hash)

    assert redeemed is not None
    assert redeemed.id == invitation.id
    assert redeemed.redeemed_at is not None


def test_redeem_if_valid_only_redeems_once(db):
    user = create_test_user(db)
    group = create_test_group(db)
    invitation = create_test_invitation(db, group, user)

    repository = GroupInvitationRepository(db)

    first_redeem = repository.redeem_if_valid(
        invitation.token_hash
    )
    second_redeem = repository.redeem_if_valid(
        invitation.token_hash
    )

    assert first_redeem is not None
    assert second_redeem is None


def test_redeem_if_valid_rejects_unknown_token(db):
    repository = GroupInvitationRepository(db)

    result = repository.redeem_if_valid(uuid4().hex)

    assert result is None


def test_redeem_if_valid_rejects_expired_invitation(db):
    user = create_test_user(db)
    group = create_test_group(db)
    invitation = create_test_invitation(
        db,
        group,
        user,
        expires_at=datetime.now(timezone.utc)
        - timedelta(seconds=1),
    )

    repository = GroupInvitationRepository(db)

    result = repository.redeem_if_valid(invitation.token_hash)

    assert result is None


def test_redeem_if_valid_rejects_revoked_invitation(db):
    user = create_test_user(db)
    group = create_test_group(db)
    invitation = create_test_invitation(db, group, user)

    invitation.revoked_at = datetime.now(timezone.utc)
    db.flush()

    repository = GroupInvitationRepository(db)

    result = repository.redeem_if_valid(invitation.token_hash)

    assert result is None


def test_redeem_if_valid_rejects_already_redeemed_invitation(db):
    user = create_test_user(db)
    group = create_test_group(db)
    invitation = create_test_invitation(db, group, user)

    invitation.redeemed_at = datetime.now(timezone.utc)
    db.flush()

    repository = GroupInvitationRepository(db)

    result = repository.redeem_if_valid(invitation.token_hash)

    assert result is None


def test_revoke_if_valid_marks_invitation_revoked(db):
    user = create_test_user(db)
    group = create_test_group(db)
    invitation = create_test_invitation(db, group, user)

    repository = GroupInvitationRepository(db)
    revoked = repository.revoke_if_valid(
        invitation.id,
        group.id,
    )

    assert revoked is not None
    assert revoked.id == invitation.id
    assert revoked.revoked_at is not None


def test_revoke_if_valid_rejects_wrong_group(db):
    user = create_test_user(db)
    group = create_test_group(db)
    other_group = create_test_group(db)
    invitation = create_test_invitation(db, group, user)

    repository = GroupInvitationRepository(db)

    result = repository.revoke_if_valid(
        invitation.id,
        other_group.id,
    )

    assert result is None


def test_revoke_if_valid_rejects_expired_invitation(db):
    user = create_test_user(db)
    group = create_test_group(db)
    invitation = create_test_invitation(
        db,
        group,
        user,
        expires_at=datetime.now(timezone.utc)
        - timedelta(seconds=1),
    )

    repository = GroupInvitationRepository(db)

    result = repository.revoke_if_valid(
        invitation.id,
        group.id,
    )

    assert result is None


def test_revoke_if_valid_rejects_already_redeemed_invitation(db):
    user = create_test_user(db)
    group = create_test_group(db)
    invitation = create_test_invitation(db, group, user)

    invitation.redeemed_at = datetime.now(timezone.utc)
    db.flush()

    repository = GroupInvitationRepository(db)

    result = repository.revoke_if_valid(
        invitation.id,
        group.id,
    )

    assert result is None


def test_revoke_if_valid_rejects_already_revoked_invitation(db):
    user = create_test_user(db)
    group = create_test_group(db)
    invitation = create_test_invitation(db, group, user)

    invitation.revoked_at = datetime.now(timezone.utc)
    db.flush()

    repository = GroupInvitationRepository(db)

    result = repository.revoke_if_valid(
        invitation.id,
        group.id,
    )

    assert result is None


def test_revoke_if_valid_rejects_unknown_invitation(db):
    group = create_test_group(db)
    repository = GroupInvitationRepository(db)

    result = repository.revoke_if_valid(
        uuid4(),
        group.id,
    )

    assert result is None