from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.auth.jwt import get_current_user_id
from app.schemas.group_activity_schema import (
    GroupActivityCreate,
    GroupActivityRead,
)
from app.services.dependencies import get_group_activity_service
from app.services.group_activity_service import GroupActivityService


router = APIRouter(prefix="/groups", tags=["group-activities"])


def _raise_activity_error(error: ValueError) -> None:
    message = str(error)

    if "not found" in message.lower():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=message,
        ) from error

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=message,
    ) from error


@router.post(
    "/{group_id}/activities",
    response_model=GroupActivityRead,
    status_code=status.HTTP_201_CREATED,
)
def create_activity(
    group_id: UUID,
    payload: GroupActivityCreate,
    user_id: UUID = Depends(get_current_user_id),
    service: GroupActivityService = Depends(get_group_activity_service),
):
    try:
        return service.create_activity(
            group_id=group_id,
            user_id=user_id,
            activity_type=payload.activity_type,
            title=payload.title,
            description=payload.description,
        )
    except ValueError as error:
        _raise_activity_error(error)


@router.get(
    "/{group_id}/activities",
    response_model=list[GroupActivityRead],
)
def get_group_activities(
    group_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: GroupActivityService = Depends(get_group_activity_service),
):
    try:
        return service.get_group_activities(group_id, user_id)
    except ValueError as error:
        _raise_activity_error(error)


@router.get(
    "/{group_id}/activities/{activity_id}",
    response_model=GroupActivityRead,
)
def get_activity(
    group_id: UUID,
    activity_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: GroupActivityService = Depends(get_group_activity_service),
):
    try:
        activity = service.get_activity(activity_id, user_id)
    except ValueError as error:
        _raise_activity_error(error)

    if activity.group_id != group_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group activity not found",
        )

    return activity


@router.delete(
    "/{group_id}/activities/{activity_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_activity(
    group_id: UUID,
    activity_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: GroupActivityService = Depends(get_group_activity_service),
):
    try:
        activity = service.get_activity(activity_id, user_id)

        if activity.group_id != group_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Group activity not found",
            )

        service.delete_activity(activity_id, user_id)
    except ValueError as error:
        _raise_activity_error(error)

    return Response(status_code=status.HTTP_204_NO_CONTENT)