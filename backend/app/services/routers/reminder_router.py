from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.auth.jwt import get_current_user_id
from app.schemas.reminder_schema import (
    ReminderCompletionUpdate,
    ReminderCreate,
    ReminderResponse,
    ReminderUpdate,
)
from app.services.dependencies import get_reminder_service
from app.services.reminder_service import (
    ReminderNotFoundError,
    ReminderService,
    ReminderValidationError,
)

router = APIRouter(prefix="/reminders", tags=["Reminders"])


def _raise_validation_error(error: ReminderValidationError) -> None:
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=str(error),
    ) from error


@router.post(
    "",
    response_model=ReminderResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_reminder(
    payload: ReminderCreate,
    user_id: UUID = Depends(get_current_user_id),
    service: ReminderService = Depends(get_reminder_service),
):
    try:
        return service.create(
            user_id,
            payload.title,
            payload.remind_at,
        )
    except ReminderValidationError as error:
        _raise_validation_error(error)


@router.get("", response_model=list[ReminderResponse])
def list_reminders(
    completed: bool | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user_id: UUID = Depends(get_current_user_id),
    service: ReminderService = Depends(get_reminder_service),
):
    try:
        return service.list_for_user(
            user_id,
            limit=limit,
            offset=offset,
            completed=completed,
        )
    except ReminderValidationError as error:
        _raise_validation_error(error)


@router.patch(
    "/{reminder_id}",
    response_model=ReminderResponse,
)
def update_reminder(
    reminder_id: UUID,
    payload: ReminderUpdate,
    user_id: UUID = Depends(get_current_user_id),
    service: ReminderService = Depends(get_reminder_service),
):
    try:
        return service.update(
            user_id,
            reminder_id,
            title=payload.title,
            remind_at=payload.remind_at,
        )
    except ReminderNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found.",
        ) from error
    except ReminderValidationError as error:
        _raise_validation_error(error)


@router.patch(
    "/{reminder_id}/completion",
    response_model=ReminderResponse,
)
def update_reminder_completion(
    reminder_id: UUID,
    payload: ReminderCompletionUpdate,
    user_id: UUID = Depends(get_current_user_id),
    service: ReminderService = Depends(get_reminder_service),
):
    try:
        return service.set_completed(
            user_id,
            reminder_id,
            completed=payload.completed,
        )
    except ReminderNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found.",
        ) from error


@router.delete(
    "/{reminder_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_reminder(
    reminder_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: ReminderService = Depends(get_reminder_service),
):
    try:
        service.delete(user_id, reminder_id)
    except ReminderNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found.",
        ) from error

    return Response(status_code=status.HTTP_204_NO_CONTENT)