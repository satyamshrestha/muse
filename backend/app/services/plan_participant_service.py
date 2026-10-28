from uuid import UUID

from sqlalchemy.orm import Session

from app.models.plan import Plan
from app.models.plan_participant import PlanParticipant
from app.repositories.group_membership_repository import (
    GroupMembershipRepository,
)
from app.repositories.plan_participant_repository import (
    PlanParticipantRepository,
)
from app.repositories.plan_repository import PlanRepository


class PlanParticipantService:
    VALID_RESPONSE_STATUSES = {"accepted", "declined"}

    def __init__(self, db: Session):
        self.db = db
        self.plan_repository = PlanRepository(db)
        self.participant_repository = PlanParticipantRepository(db)
        self.membership_repository = GroupMembershipRepository(db)

    def _get_plan(self, plan_id: UUID) -> Plan:
        plan = self.plan_repository.get_by_id(plan_id)

        if plan is None:
            raise ValueError("Plan not found")

        return plan

    def _ensure_group_member(
        self,
        group_id: UUID,
        user_id: UUID,
    ) -> None:
        if not self.membership_repository.is_member(
            user_id=user_id,
            group_id=group_id,
        ):
            raise ValueError("User is not a member of this group")

    def invite_participant(
        self,
        plan_id: UUID,
        requester_id: UUID,
        participant_user_id: UUID,
    ) -> PlanParticipant:
        plan = self._get_plan(plan_id)

        self._ensure_group_member(plan.group_id, requester_id)

        if plan.created_by != requester_id:
            raise ValueError(
                "Only the plan creator can invite participants"
            )

        self._ensure_group_member(
            plan.group_id,
            participant_user_id,
        )

        existing = self.participant_repository.get_for_user_and_plan(
            user_id=participant_user_id,
            plan_id=plan_id,
        )

        if existing is not None:
            raise ValueError(
                "User has already been invited to this plan"
            )

        participant = self.participant_repository.create(
            plan_id=plan_id,
            user_id=participant_user_id,
        )
        self.db.commit()
        self.db.refresh(participant)
        return participant

    def list_participants(
        self,
        plan_id: UUID,
        user_id: UUID,
    ) -> list[PlanParticipant]:
        plan = self._get_plan(plan_id)
        self._ensure_group_member(plan.group_id, user_id)

        return self.participant_repository.get_for_plan(plan_id)

    def respond_to_invitation(
        self,
        plan_id: UUID,
        user_id: UUID,
        status: str,
    ) -> PlanParticipant:
        plan = self._get_plan(plan_id)
        self._ensure_group_member(plan.group_id, user_id)

        if status not in self.VALID_RESPONSE_STATUSES:
            raise ValueError(
                "Status must be either 'accepted' or 'declined'"
            )

        participant = (
            self.participant_repository.get_for_user_and_plan(
                user_id=user_id,
                plan_id=plan_id,
            )
        )

        if participant is None:
            raise ValueError("Plan participant not found")

        updated = self.participant_repository.update_status(
            participant,
            status=status,
        )
        self.db.commit()
        self.db.refresh(updated)
        return updated

    def remove_participant(
        self,
        plan_id: UUID,
        requester_id: UUID,
        participant_user_id: UUID,
    ) -> bool:
        plan = self._get_plan(plan_id)
        self._ensure_group_member(plan.group_id, requester_id)

        if plan.created_by != requester_id:
            raise ValueError(
                "Only the plan creator can remove participants"
            )

        participant = (
            self.participant_repository.get_for_user_and_plan(
                user_id=participant_user_id,
                plan_id=plan_id,
            )
        )

        if participant is None:
            raise ValueError("Plan participant not found")

        deleted = self.participant_repository.delete(participant.id)

        if deleted:
            self.db.commit()

        return deleted