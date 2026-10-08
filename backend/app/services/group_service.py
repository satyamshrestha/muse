from uuid import UUID

from app.repositories.friend_group_repository import (
    FriendGroupRepository,
)
from app.repositories.group_membership_repository import (
    GroupMembershipRepository,
)


class GroupService:
    def __init__(
        self,
        group_repository: FriendGroupRepository,
        membership_repository: GroupMembershipRepository,
    ):
        self.group_repository = group_repository
        self.membership_repository = membership_repository

    def create_group(
        self,
        user_id: UUID,
        name: str,
    ):
        group = self.group_repository.create(
            name=name,
        )

        self.membership_repository.create(
            user_id=user_id,
            group_id=group.id,
        )

        self.group_repository.db.commit()
        self.group_repository.db.refresh(group)

        return group