from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.group_activity import GroupActivity


class GroupActivityRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        group_id: UUID,
        created_by: UUID,
        activity_type: str,
        title: str,
        description: str | None = None,
    ) -> GroupActivity:
        activity = GroupActivity(
            group_id=group_id,
            created_by=created_by,
            activity_type=activity_type,
            title=title,
            description=description,
        )
        self.db.add(activity)
        self.db.flush()
        return activity

    def get_by_id(
        self,
        activity_id: UUID,
    ) -> GroupActivity | None:
        return self.db.scalar(
            select(GroupActivity).where(
                GroupActivity.id == activity_id
            )
        )

    def get_for_group(
        self,
        group_id: UUID,
    ) -> list[GroupActivity]:
        statement = (
            select(GroupActivity)
            .where(GroupActivity.group_id == group_id)
            .order_by(GroupActivity.created_at.desc())
        )
        return list(self.db.scalars(statement))

    def delete(self, activity_id: UUID) -> bool:
        result = self.db.execute(
            delete(GroupActivity).where(
                GroupActivity.id == activity_id
            )
        )
        self.db.flush()
        return result.rowcount > 0