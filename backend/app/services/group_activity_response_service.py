from uuid import UUID

from sqlalchemy.orm import Session

from app.models.group_activity_response import GroupActivityResponse
from app.repositories.group_activity_repository import GroupActivityRepository
from app.repositories.group_activity_response_repository import (
    GroupActivityResponseRepository,
)
from app.repositories.group_membership_repository import GroupMembershipRepository


class GroupActivityResponseService:
    def __init__(self, db: Session):
        self.db = db
        self.response_repository = GroupActivityResponseRepository(db)
        self.activity_repository = GroupActivityRepository(db)
        self.membership_repository = GroupMembershipRepository(db)

    def create_response(
        self,
        activity_id: UUID,
        user_id: UUID,
        response: str,
        note: str | None = None,
    ) -> GroupActivityResponse:
        activity = self.activity_repository.get_by_id(activity_id)

        if activity is None:
            raise ValueError("Group activity not found")

        if not self.membership_repository.is_member(
            user_id, activity.group_id
        ):
            raise ValueError("User is not a member of this group")

        existing = self.response_repository.get_for_user_and_activity(
            user_id=user_id,
            activity_id=activity_id,
        )

        if existing is not None:
            raise ValueError("User has already responded to this activity")

        activity_response = self.response_repository.create(
            activity_id=activity_id,
            user_id=user_id,
            response=response,
            note=note,
        )
        self.db.commit()
        self.db.refresh(activity_response)
        return activity_response

    def get_response(
        self,
        response_id: UUID,
        user_id: UUID,
    ) -> GroupActivityResponse:
        activity_response = self.response_repository.get_by_id(response_id)

        if activity_response is None:
            raise ValueError("Group activity response not found")

        activity = self.activity_repository.get_by_id(
            activity_response.activity_id
        )

        if activity is None:
            raise ValueError("Group activity not found")

        if not self.membership_repository.is_member(
            user_id, activity.group_id
        ):
            raise ValueError("User is not a member of this group")

        return activity_response

    def get_activity_responses(
        self,
        activity_id: UUID,
        user_id: UUID,
    ) -> list[GroupActivityResponse]:
        activity = self.activity_repository.get_by_id(activity_id)

        if activity is None:
            raise ValueError("Group activity not found")

        if not self.membership_repository.is_member(
            user_id, activity.group_id
        ):
            raise ValueError("User is not a member of this group")

        return self.response_repository.get_for_activity(activity_id)

    def delete_response(
        self,
        response_id: UUID,
        user_id: UUID,
    ) -> bool:
        activity_response = self.response_repository.get_by_id(response_id)

        if activity_response is None:
            raise ValueError("Group activity response not found")

        if activity_response.user_id != user_id:
            raise ValueError("Only the response creator can delete it")

        deleted = self.response_repository.delete(response_id)

        if deleted:
            self.db.commit()

        return deleted