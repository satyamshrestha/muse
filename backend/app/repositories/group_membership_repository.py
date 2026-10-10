from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.friend_group import FriendGroup
from app.models.group_membership import GroupMembership


class GroupMembershipRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        user_id: UUID,
        group_id: UUID,
    ) -> GroupMembership:
        membership = GroupMembership(
            user_id=user_id,
            group_id=group_id,
        )
        self.db.add(membership)
        self.db.flush()
        return membership

    def get_groups_for_user(
        self,
        user_id: UUID,
    ) -> list[FriendGroup]:
        statement = (
            select(FriendGroup)
            .join(
                GroupMembership,
                GroupMembership.group_id == FriendGroup.id,
            )
            .where(GroupMembership.user_id == user_id)
            .order_by(FriendGroup.created_at.desc())
        )

        return list(self.db.scalars(statement))

    def is_member(
        self,
        user_id: UUID,
        group_id: UUID,
    ) -> bool:
        statement = select(GroupMembership).where(
            GroupMembership.user_id == user_id,
            GroupMembership.group_id == group_id,
        )
        return self.db.scalar(statement) is not None

    def get_membership(
        self,
        user_id: UUID,
        group_id: UUID,
    ) -> GroupMembership | None:
        statement = select(GroupMembership).where(
            GroupMembership.user_id == user_id,
            GroupMembership.group_id == group_id,
        )
        return self.db.scalar(statement)