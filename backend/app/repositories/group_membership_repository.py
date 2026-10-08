from uuid import UUID

from sqlalchemy.orm import Session

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