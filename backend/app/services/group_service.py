import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException

from app.exceptions.group_exceptions import (
    AlreadyGroupMemberException,
    GroupNotFoundException,
)
from app.models.friend_group import FriendGroup
from app.repositories.friend_group_repository import FriendGroupRepository
from app.repositories.group_membership_repository import GroupMembershipRepository
from app.repositories.group_invitation_repository import GroupInvitationRepository


class GroupService:
    INVITATION_LIFETIME = timedelta(days=7)

    def __init__(
        self,
        group_repository: FriendGroupRepository,
        membership_repository: GroupMembershipRepository,
        invitation_repository: GroupInvitationRepository,
    ):
        self.group_repository = group_repository
        self.membership_repository = membership_repository
        self.invitation_repository = invitation_repository

    def create_group(self, user_id: UUID, name: str) -> FriendGroup:
        db = self.group_repository.db
        try:
            group = self.group_repository.create(name=name)
            self.membership_repository.create(
                user_id=user_id,
                group_id=group.id,
            )
            db.commit()
            db.refresh(group)
            return group
        except Exception:
            db.rollback()
            raise

    def get_user_groups(self, user_id: UUID) -> list[FriendGroup]:
        return self.membership_repository.get_groups_for_user(user_id)

    def get_group(self, user_id: UUID, group_id: UUID) -> FriendGroup:
        group = self.group_repository.get_by_id(group_id)
        if (
            group is None
            or not self.membership_repository.is_member(
                user_id=user_id,
                group_id=group_id,
            )
        ):
            raise GroupNotFoundException()
        return group

    def get_group_members(self, user_id: UUID, group_id: UUID):
        group = self.group_repository.get_by_id(group_id)
        if (
            group is None
            or not self.membership_repository.is_member(
                user_id=user_id,
                group_id=group_id,
            )
        ):
            raise GroupNotFoundException()

        return self.membership_repository.get_members_for_group(
            group_id=group_id
        )

    def create_invitation(self, user_id: UUID, group_id: UUID) -> dict:
        db = self.group_repository.db

        group = self.group_repository.get_by_id(group_id)
        if (
            group is None
            or not self.membership_repository.is_member(
                user_id=user_id,
                group_id=group_id,
            )
        ):
            raise GroupNotFoundException()

        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        expires_at = datetime.now(timezone.utc) + self.INVITATION_LIFETIME

        try:
            self.invitation_repository.create(
                group_id=group_id,
                created_by=user_id,
                token_hash=token_hash,
                expires_at=expires_at,
            )
            db.commit()
        except Exception:
            db.rollback()
            raise

        return {"token": token, "expires_at": expires_at}

    def revoke_invitation(
        self,
        user_id: UUID,
        group_id: UUID,
        invitation_id: UUID,
    ) -> None:
        db = self.group_repository.db

        try:
            group = self.group_repository.get_by_id(group_id)
            if (
                group is None
                or not self.membership_repository.is_member(
                    user_id=user_id,
                    group_id=group_id,
                )
            ):
                raise GroupNotFoundException()

            invitation = self.invitation_repository.revoke_if_valid(
                invitation_id=invitation_id,
                group_id=group_id,
            )

            if invitation is None:
                raise HTTPException(
                    status_code=404,
                    detail="Invitation not found or no longer valid",
                )

            db.commit()
        except Exception:
            db.rollback()
            raise

    def join_group_with_invitation(
        self,
        user_id: UUID,
        token: str,
    ) -> FriendGroup:
        db = self.group_repository.db
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()

        try:
            invitation = self.invitation_repository.redeem_if_valid(
                token_hash=token_hash
            )

            if invitation is None:
                raise HTTPException(
                    status_code=404,
                    detail="Invitation not found or no longer valid",
                )

            group = self.group_repository.get_by_id(invitation.group_id)
            if group is None:
                raise HTTPException(
                    status_code=404,
                    detail="Invitation not found or no longer valid",
                )

            if self.membership_repository.is_member(
                user_id=user_id,
                group_id=invitation.group_id,
            ):
                raise AlreadyGroupMemberException()

            self.membership_repository.create(
                user_id=user_id,
                group_id=invitation.group_id,
            )

            db.commit()
            return group

        except Exception:
            db.rollback()
            raise

    def leave_group(self, user_id: UUID, group_id: UUID) -> None:
        db = self.group_repository.db

        try:
            group = self.group_repository.get_by_id(group_id)
            if (
                group is None
                or not self.membership_repository.is_member(
                    user_id=user_id,
                    group_id=group_id,
                )
            ):
                raise GroupNotFoundException()

            self.membership_repository.delete_membership(
                user_id=user_id,
                group_id=group_id,
            )

            remaining_members = (
                self.membership_repository.get_members_for_group(
                    group_id=group_id
                )
            )
            if not remaining_members:
                self.group_repository.delete(group_id)

            db.commit()
        except Exception:
            db.rollback()
            raise