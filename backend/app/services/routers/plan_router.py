from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.auth.jwt import get_current_user_id
from app.schemas.plan_schema import PlanCreate, PlanRead, PlanUpdate
from app.services.dependencies import get_plan_service
from app.services.plan_service import PlanService


router = APIRouter(prefix="/groups", tags=["plans"])


def _raise_plan_error(error: ValueError) -> None:
    message = str(error)
    lowered = message.lower()

    if "not found" in lowered:
        code = status.HTTP_404_NOT_FOUND
    elif "limit must" in lowered or "offset cannot" in lowered:
        code = status.HTTP_422_UNPROCESSABLE_ENTITY
    elif "cannot be before" in lowered:
        code = status.HTTP_422_UNPROCESSABLE_ENTITY
    else:
        code = status.HTTP_403_FORBIDDEN

    raise HTTPException(status_code=code, detail=message) from error


@router.post(
    "/{group_id}/plans",
    response_model=PlanRead,
    status_code=status.HTTP_201_CREATED,
)
def create_plan(
    group_id: UUID,
    payload: PlanCreate,
    user_id: UUID = Depends(get_current_user_id),
    service: PlanService = Depends(get_plan_service),
):
    try:
        return service.create_plan(
            group_id=group_id,
            user_id=user_id,
            title=payload.title,
            description=payload.description,
            starts_at=payload.starts_at,
            ends_at=payload.ends_at,
        )
    except ValueError as error:
        _raise_plan_error(error)


@router.get(
    "/{group_id}/plans",
    response_model=list[PlanRead],
)
def list_plans(
    group_id: UUID,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user_id: UUID = Depends(get_current_user_id),
    service: PlanService = Depends(get_plan_service),
):
    try:
        return service.list_plans(
            group_id=group_id,
            user_id=user_id,
            limit=limit,
            offset=offset,
        )
    except ValueError as error:
        _raise_plan_error(error)


@router.get(
    "/{group_id}/plans/{plan_id}",
    response_model=PlanRead,
)
def get_plan(
    group_id: UUID,
    plan_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: PlanService = Depends(get_plan_service),
):
    try:
        return service.get_plan(
            group_id=group_id,
            plan_id=plan_id,
            user_id=user_id,
        )
    except ValueError as error:
        _raise_plan_error(error)


@router.put(
    "/{group_id}/plans/{plan_id}",
    response_model=PlanRead,
)
def update_plan(
    group_id: UUID,
    plan_id: UUID,
    payload: PlanUpdate,
    user_id: UUID = Depends(get_current_user_id),
    service: PlanService = Depends(get_plan_service),
):
    try:
        return service.update_plan(
            group_id=group_id,
            plan_id=plan_id,
            user_id=user_id,
            title=payload.title,
            description=payload.description,
            starts_at=payload.starts_at,
            ends_at=payload.ends_at,
        )
    except ValueError as error:
        _raise_plan_error(error)


@router.delete(
    "/{group_id}/plans/{plan_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_plan(
    group_id: UUID,
    plan_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: PlanService = Depends(get_plan_service),
):
    try:
        service.delete_plan(
            group_id=group_id,
            plan_id=plan_id,
            user_id=user_id,
        )
    except ValueError as error:
        _raise_plan_error(error)

    return Response(status_code=status.HTTP_204_NO_CONTENT)