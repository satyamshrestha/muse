from uuid import UUID

from sqlalchemy.orm import Session

from app.repositories.friend_group_repository import FriendGroupRepository
from app.repositories.group_activity_repository import GroupActivityRepository
from app.repositories.group_membership_repository import GroupMembershipRepository


class GroupActivityService:
    def __init__(self, db: Session):
        self.db = db
        self.activity_repository = GroupActivityRepository(db)
        self.group_repository = FriendGroupRepository(db)
        self.membership_repository = GroupMembershipRepository(db)

    def create_activity(
        self,
        group_id: UUID,
        user_id: UUID,
        activity_type: str,
        title: str,
        description: str | None = None,
    ):
        group = self.group_repository.get_by_id(group_id)

        if group is None:
            raise ValueError("Group not found")

        if not self.membership_repository.is_member(user_id, group_id):
            raise ValueError("User is not a member of this group")

        activity = self.activity_repository.create(
            group_id=group_id,
            created_by=user_id,
            activity_type=activity_type,
            title=title,
            description=description,
        )
        self.db.commit()
        self.db.refresh(activity)
        return activity

    def get_activity(self, activity_id: UUID, user_id: UUID):
        activity = self.activity_repository.get_by_id(activity_id)

        if activity is None:
            raise ValueError("Group activity not found")

        if not self.membership_repository.is_member(
            user_id, activity.group_id
        ):
            raise ValueError("User is not a member of this group")

        return activity

    def get_group_activities(self, group_id: UUID, user_id: UUID):
        group = self.group_repository.get_by_id(group_id)

        if group is None:
            raise ValueError("Group not found")

        if not self.membership_repository.is_member(user_id, group_id):
            raise ValueError("User is not a member of this group")

        return self.activity_repository.get_for_group(group_id)

    def delete_activity(self, activity_id: UUID, user_id: UUID) -> bool:
        activity = self.activity_repository.get_by_id(activity_id)

        if activity is None:
            raise ValueError("Group activity not found")

        if activity.created_by != user_id:
            raise ValueError("Only the activity creator can delete it")

        deleted = self.activity_repository.delete(activity_id)

        if deleted:
            self.db.commit()

        return deleted