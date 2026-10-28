from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.auth.jwt import get_current_user_id
from app.schemas.plan_participant_schema import (
    PlanParticipantCreate,
    PlanParticipantRead,
    PlanParticipantRespond,
)
from app.services.dependencies import get_plan_participant_service
from app.services.plan_participant_service import PlanParticipantService

router = APIRouter(
    prefix="/groups",
    tags=["plan-participants"],
)


def _ensure_plan_belongs_to_group(
    service: PlanParticipantService,
    group_id: UUID,
    plan_id: UUID,
) -> None:
    plan = service.plan_repository.get_by_id(plan_id)

    if plan is None or plan.group_id != group_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found",
        )


def _raise_participant_error(error: ValueError) -> None:
    message = str(error)
    lowered = message.lower()

    if "not found" in lowered:
        code = status.HTTP_404_NOT_FOUND
    elif "already been invited" in lowered:
        code = status.HTTP_409_CONFLICT
    elif "status must" in lowered:
        code = status.HTTP_422_UNPROCESSABLE_ENTITY
    else:
        code = status.HTTP_403_FORBIDDEN

    raise HTTPException(status_code=code, detail=message) from error


@router.post(
    "/{group_id}/plans/{plan_id}/participants",
    response_model=PlanParticipantRead,
    status_code=status.HTTP_201_CREATED,
)
def invite_participant(
    group_id: UUID,
    plan_id: UUID,
    payload: PlanParticipantCreate,
    user_id: UUID = Depends(get_current_user_id),
    service: PlanParticipantService = Depends(
        get_plan_participant_service
    ),
):
    _ensure_plan_belongs_to_group(service, group_id, plan_id)

    try:
        return service.invite_participant(
            plan_id=plan_id,
            requester_id=user_id,
            participant_user_id=payload.user_id,
        )
    except ValueError as error:
        _raise_participant_error(error)


@router.get(
    "/{group_id}/plans/{plan_id}/participants",
    response_model=list[PlanParticipantRead],
)
def list_participants(
    group_id: UUID,
    plan_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: PlanParticipantService = Depends(
        get_plan_participant_service
    ),
):
    _ensure_plan_belongs_to_group(service, group_id, plan_id)

    try:
        return service.list_participants(
            plan_id=plan_id,
            user_id=user_id,
        )
    except ValueError as error:
        _raise_participant_error(error)


@router.put(
    "/{group_id}/plans/{plan_id}/participants/me",
    response_model=PlanParticipantRead,
)
def respond_to_invitation(
    group_id: UUID,
    plan_id: UUID,
    payload: PlanParticipantRespond,
    user_id: UUID = Depends(get_current_user_id),
    service: PlanParticipantService = Depends(
        get_plan_participant_service
    ),
):
    _ensure_plan_belongs_to_group(service, group_id, plan_id)

    try:
        return service.respond_to_invitation(
            plan_id=plan_id,
            user_id=user_id,
            status=payload.status,
        )
    except ValueError as error:
        _raise_participant_error(error)


@router.delete(
    "/{group_id}/plans/{plan_id}/participants/{participant_user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_participant(
    group_id: UUID,
    plan_id: UUID,
    participant_user_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: PlanParticipantService = Depends(
        get_plan_participant_service
    ),
):
    _ensure_plan_belongs_to_group(service, group_id, plan_id)

    try:
        service.remove_participant(
            plan_id=plan_id,
            requester_id=user_id,
            participant_user_id=participant_user_id,
        )
    except ValueError as error:
        _raise_participant_error(error)

    return Response(status_code=status.HTTP_204_NO_CONTENT)