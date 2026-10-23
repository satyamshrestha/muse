from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.group_activity_response import GroupActivityResponse


class GroupActivityResponseRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        activity_id: UUID,
        user_id: UUID,
        response: str,
        note: str | None = None,
    ) -> GroupActivityResponse:
        activity_response = GroupActivityResponse(
            activity_id=activity_id,
            user_id=user_id,
            response=response,
            note=note,
        )
        self.db.add(activity_response)
        self.db.flush()
        return activity_response

    def get_by_id(
        self,
        response_id: UUID,
    ) -> GroupActivityResponse | None:
        return self.db.scalar(
            select(GroupActivityResponse).where(
                GroupActivityResponse.id == response_id
            )
        )

    def get_for_activity(
        self,
        activity_id: UUID,
    ) -> list[GroupActivityResponse]:
        statement = (
            select(GroupActivityResponse)
            .where(GroupActivityResponse.activity_id == activity_id)
            .order_by(GroupActivityResponse.created_at.desc())
        )
        return list(self.db.scalars(statement))

    def get_for_user_and_activity(
        self,
        user_id: UUID,
        activity_id: UUID,
    ) -> GroupActivityResponse | None:
        statement = select(GroupActivityResponse).where(
            GroupActivityResponse.user_id == user_id,
            GroupActivityResponse.activity_id == activity_id,
        )
        return self.db.scalar(statement)

    def delete(self, response_id: UUID) -> bool:
        result = self.db.execute(
            delete(GroupActivityResponse).where(
                GroupActivityResponse.id == response_id
            )
        )
        self.db.flush()
        return result.rowcount > 0