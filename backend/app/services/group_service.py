from uuid import UUID

from app.exceptions.group_exceptions import GroupNotFoundException
from app.repositories.friend_group_repository import (
    FriendGroupRepository,
)
from app.repositories.group_membership_repository import (
    GroupMembershipRepository,
)
from app.models.friend_group import FriendGroup


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
    ) -> FriendGroup:
        group = self.group_repository.create(name=name)

        self.membership_repository.create(
            user_id=user_id,
            group_id=group.id,
        )

        self.group_repository.db.commit()
        self.group_repository.db.refresh(group)

        return group

    def get_user_groups(
        self,
        user_id: UUID,
    ) -> list[FriendGroup]:
        return self.membership_repository.get_groups_for_user(
            user_id
        )

    def get_group(
        self,
        user_id: UUID,
        group_id: UUID,
    ) -> FriendGroup:
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