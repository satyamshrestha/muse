from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.plan import Plan
from app.repositories.friend_group_repository import FriendGroupRepository
from app.repositories.group_membership_repository import (
    GroupMembershipRepository,
)
from app.repositories.plan_repository import PlanRepository


class PlanService:
    def __init__(self, db: Session):
        self.db = db
        self.plan_repository = PlanRepository(db)
        self.group_repository = FriendGroupRepository(db)
        self.membership_repository = GroupMembershipRepository(db)

    def _ensure_group_member(
        self,
        group_id: UUID,
        user_id: UUID,
    ) -> None:
        group = self.group_repository.get_by_id(group_id)

        if group is None:
            raise ValueError("Group not found")

        if not self.membership_repository.is_member(
            user_id=user_id,
            group_id=group_id,
        ):
            raise ValueError("User is not a member of this group")

    @staticmethod
    def _validate_schedule(
        starts_at: datetime | None,
        ends_at: datetime | None,
    ) -> None:
        if (
            starts_at is not None
            and ends_at is not None
            and ends_at < starts_at
        ):
            raise ValueError("Plan end time cannot be before its start time")

    def create_plan(
        self,
        group_id: UUID,
        user_id: UUID,
        title: str,
        description: str | None = None,
        starts_at: datetime | None = None,
        ends_at: datetime | None = None,
    ) -> Plan:
        self._ensure_group_member(group_id, user_id)
        self._validate_schedule(starts_at, ends_at)

        plan = self.plan_repository.create(
            group_id=group_id,
            created_by=user_id,
            title=title,
            description=description,
            starts_at=starts_at,
            ends_at=ends_at,
        )
        self.db.commit()
        self.db.refresh(plan)
        return plan

    def get_plan(
        self,
        group_id: UUID,
        plan_id: UUID,
        user_id: UUID,
    ) -> Plan:
        self._ensure_group_member(group_id, user_id)

        plan = self.plan_repository.get_by_id(plan_id)

        if plan is None or plan.group_id != group_id:
            raise ValueError("Plan not found")

        return plan

    def list_plans(
        self,
        group_id: UUID,
        user_id: UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Plan]:
        self._ensure_group_member(group_id, user_id)

        if limit < 1 or limit > 100:
            raise ValueError("Limit must be between 1 and 100")

        if offset < 0:
            raise ValueError("Offset cannot be negative")

        return self.plan_repository.list_by_group(
            group_id=group_id,
            limit=limit,
            offset=offset,
        )

    def update_plan(
        self,
        group_id: UUID,
        plan_id: UUID,
        user_id: UUID,
        *,
        title: str,
        description: str | None,
        starts_at: datetime | None = None,
        ends_at: datetime | None = None,
    ) -> Plan:
        self._ensure_group_member(group_id, user_id)

        plan = self.plan_repository.get_by_id(plan_id)

        if plan is None or plan.group_id != group_id:
            raise ValueError("Plan not found")

        if plan.created_by != user_id:
            raise ValueError("Only the plan creator can update it")

        self._validate_schedule(starts_at, ends_at)

        updated_plan = self.plan_repository.update(
            plan,
            title=title,
            description=description,
            starts_at=starts_at,
            ends_at=ends_at,
        )
        self.db.commit()
        self.db.refresh(updated_plan)
        return updated_plan

    def delete_plan(
        self,
        group_id: UUID,
        plan_id: UUID,
        user_id: UUID,
    ) -> bool:
        self._ensure_group_member(group_id, user_id)

        plan = self.plan_repository.get_by_id(plan_id)

        if plan is None or plan.group_id != group_id:
            raise ValueError("Plan not found")

        if plan.created_by != user_id:
            raise ValueError("Only the plan creator can delete it")

        self.plan_repository.delete(plan)
        self.db.commit()
        return True