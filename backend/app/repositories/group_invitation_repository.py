from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import update
from sqlalchemy.orm import Session

from app.models.group_invitation import GroupInvitation


class GroupInvitationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        group_id: UUID,
        created_by: UUID,
        token_hash: str,
        expires_at: datetime,
    ) -> GroupInvitation:
        invitation = GroupInvitation(
            group_id=group_id,
            created_by=created_by,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self.db.add(invitation)
        self.db.flush()
        return invitation

    def redeem_if_valid(
        self,
        token_hash: str,
    ) -> GroupInvitation | None:
        now = datetime.now(timezone.utc)

        statement = (
            update(GroupInvitation)
            .where(
                GroupInvitation.token_hash == token_hash,
                GroupInvitation.redeemed_at.is_(None),
                GroupInvitation.revoked_at.is_(None),
                GroupInvitation.expires_at > now,
            )
            .values(redeemed_at=now)
            .returning(GroupInvitation)
        )

        return self.db.scalars(statement).one_or_none()

    def revoke_if_valid(
        self,
        invitation_id: UUID,
        group_id: UUID,
    ) -> GroupInvitation | None:
        now = datetime.now(timezone.utc)

        statement = (
            update(GroupInvitation)
            .where(
                GroupInvitation.id == invitation_id,
                GroupInvitation.group_id == group_id,
                GroupInvitation.redeemed_at.is_(None),
                GroupInvitation.revoked_at.is_(None),
                GroupInvitation.expires_at > now,
            )
            .values(revoked_at=now)
            .returning(GroupInvitation)
        )

        return self.db.scalars(statement).one_or_none()