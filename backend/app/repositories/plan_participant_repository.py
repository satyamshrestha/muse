from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.plan_participant import PlanParticipant


class PlanParticipantRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        plan_id: UUID,
        user_id: UUID,
        status: str = "invited",
    ) -> PlanParticipant:
        participant = PlanParticipant(
            plan_id=plan_id,
            user_id=user_id,
            status=status,
        )
        self.db.add(participant)
        self.db.flush()
        return participant

    def get_by_id(
        self,
        participant_id: UUID,
    ) -> PlanParticipant | None:
        return self.db.scalar(
            select(PlanParticipant).where(
                PlanParticipant.id == participant_id
            )
        )

    def get_for_plan(
        self,
        plan_id: UUID,
    ) -> list[PlanParticipant]:
        statement = (
            select(PlanParticipant)
            .where(PlanParticipant.plan_id == plan_id)
            .order_by(PlanParticipant.created_at.asc())
        )
        return list(self.db.scalars(statement))

    def get_for_user_and_plan(
        self,
        user_id: UUID,
        plan_id: UUID,
    ) -> PlanParticipant | None:
        statement = select(PlanParticipant).where(
            PlanParticipant.user_id == user_id,
            PlanParticipant.plan_id == plan_id,
        )
        return self.db.scalar(statement)

    def update_status(
        self,
        participant: PlanParticipant,
        *,
        status: str,
    ) -> PlanParticipant:
        participant.status = status
        self.db.flush()
        return participant

    def delete(
        self,
        participant_id: UUID,
    ) -> bool:
        result = self.db.execute(
            delete(PlanParticipant).where(
                PlanParticipant.id == participant_id
            )
        )
        self.db.flush()
        return result.rowcount > 0