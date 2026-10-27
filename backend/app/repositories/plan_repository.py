from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.plan import Plan


class PlanRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        group_id: UUID,
        created_by: UUID,
        title: str,
        description: str | None = None,
        starts_at=None,
        ends_at=None,
    ) -> Plan:
        plan = Plan(
            group_id=group_id,
            created_by=created_by,
            title=title,
            description=description,
            starts_at=starts_at,
            ends_at=ends_at,
        )
        self.db.add(plan)
        self.db.flush()
        return plan

    def get_by_id(self, plan_id: UUID) -> Plan | None:
        return self.db.scalar(
            select(Plan).where(Plan.id == plan_id)
        )

    def list_by_group(
        self,
        group_id: UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Plan]:
        return list(
            self.db.scalars(
                select(Plan)
                .where(Plan.group_id == group_id)
                .order_by(Plan.created_at.desc(), Plan.id.desc())
                .limit(limit)
                .offset(offset)
            ).all()
        )

    def update(
        self,
        plan: Plan,
        *,
        title: str,
        description: str | None,
        starts_at=None,
        ends_at=None,
    ) -> Plan:
        plan.title = title
        plan.description = description
        plan.starts_at = starts_at
        plan.ends_at = ends_at
        self.db.flush()
        return plan

    def delete(self, plan: Plan) -> None:
        self.db.execute(
            delete(Plan).where(Plan.id == plan.id)
        )
        self.db.flush()