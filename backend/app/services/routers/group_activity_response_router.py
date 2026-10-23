from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.auth.jwt import get_current_user_id
from app.schemas.group_activity_response_schema import (
    GroupActivityResponseCreate,
    GroupActivityResponseRead,
)
from app.services.dependencies import get_group_activity_response_service
from app.services.group_activity_response_service import (
    GroupActivityResponseService,
)

router = APIRouter(
    prefix="/groups",
    tags=["group-activity-responses"],
)


def _ensure_activity_belongs_to_group(
    service: GroupActivityResponseService,
    group_id: UUID,
    activity_id: UUID,
) -> None:
    activity = service.activity_repository.get_by_id(activity_id)

    if activity is None or activity.group_id != group_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group activity not found",
        )


def _raise_response_error(error: ValueError) -> None:
    message = str(error)

    if "not found" in message.lower():
        code = status.HTTP_404_NOT_FOUND
    elif "already responded" in message.lower():
        code = status.HTTP_409_CONFLICT
    else:
        code = status.HTTP_403_FORBIDDEN

    raise HTTPException(status_code=code, detail=message) from error


@router.post(
    "/{group_id}/activities/{activity_id}/responses",
    response_model=GroupActivityResponseRead,
    status_code=status.HTTP_201_CREATED,
)
def create_response(
    group_id: UUID,
    activity_id: UUID,
    payload: GroupActivityResponseCreate,
    user_id: UUID = Depends(get_current_user_id),
    service: GroupActivityResponseService = Depends(
        get_group_activity_response_service
    ),
):
    _ensure_activity_belongs_to_group(service, group_id, activity_id)

    try:
        return service.create_response(
            activity_id=activity_id,
            user_id=user_id,
            response=payload.response,
            note=payload.note,
        )
    except ValueError as error:
        _raise_response_error(error)


@router.get(
    "/{group_id}/activities/{activity_id}/responses",
    response_model=list[GroupActivityResponseRead],
)
def get_activity_responses(
    group_id: UUID,
    activity_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: GroupActivityResponseService = Depends(
        get_group_activity_response_service
    ),
):
    _ensure_activity_belongs_to_group(service, group_id, activity_id)

    try:
        return service.get_activity_responses(activity_id, user_id)
    except ValueError as error:
        _raise_response_error(error)


@router.get(
    "/{group_id}/activities/{activity_id}/responses/{response_id}",
    response_model=GroupActivityResponseRead,
)
def get_response(
    group_id: UUID,
    activity_id: UUID,
    response_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: GroupActivityResponseService = Depends(
        get_group_activity_response_service
    ),
):
    _ensure_activity_belongs_to_group(service, group_id, activity_id)

    try:
        activity_response = service.get_response(response_id, user_id)
    except ValueError as error:
        _raise_response_error(error)

    if activity_response.activity_id != activity_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group activity response not found",
        )

    return activity_response


@router.delete(
    "/{group_id}/activities/{activity_id}/responses/{response_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_response(
    group_id: UUID,
    activity_id: UUID,
    response_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: GroupActivityResponseService = Depends(
        get_group_activity_response_service
    ),
):
    _ensure_activity_belongs_to_group(service, group_id, activity_id)

    try:
        activity_response = service.get_response(response_id, user_id)

        if activity_response.activity_id != activity_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Group activity response not found",
            )

        service.delete_response(response_id, user_id)
    except ValueError as error:
        _raise_response_error(error)

    return Response(status_code=status.HTTP_204_NO_CONTENT)