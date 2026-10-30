from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select

from app.auth.jwt import get_current_user_id
from app.models.room_message import RoomMessage
from app.schemas.room_message_schema import (
    RoomMessageCreate,
    RoomMessageRead,
)
from app.services.dependencies import get_room_message_service
from app.services.room_message_service import RoomMessageService


router = APIRouter(
    prefix="/groups",
    tags=["room-messages"],
)


def _ensure_message_belongs_to_group(
    service: RoomMessageService,
    group_id: UUID,
    message_id: UUID,
) -> None:
    message = service.db.scalar(
        select(RoomMessage).where(
            RoomMessage.id == message_id,
            RoomMessage.group_id == group_id,
        )
    )

    if message is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found",
        )


def _raise_message_error(error: ValueError) -> None:
    message = str(error)
    lowered = message.lower()

    if "not found" in lowered:
        code = status.HTTP_404_NOT_FOUND
    elif "must not be empty" in lowered:
        code = status.HTTP_422_UNPROCESSABLE_ENTITY
    else:
        code = status.HTTP_403_FORBIDDEN

    raise HTTPException(
        status_code=code,
        detail=message,
    ) from error


@router.post(
    "/{group_id}/messages",
    response_model=RoomMessageRead,
    status_code=status.HTTP_201_CREATED,
)
def create_message(
    group_id: UUID,
    payload: RoomMessageCreate,
    user_id: UUID = Depends(get_current_user_id),
    service: RoomMessageService = Depends(get_room_message_service),
):
    try:
        return service.create_message(
            group_id=group_id,
            user_id=user_id,
            content=payload.content,
        )
    except ValueError as error:
        _raise_message_error(error)


@router.get(
    "/{group_id}/messages",
    response_model=list[RoomMessageRead],
)
def list_group_messages(
    group_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: RoomMessageService = Depends(get_room_message_service),
):
    try:
        return service.get_group_messages(
            group_id=group_id,
            user_id=user_id,
        )
    except ValueError as error:
        _raise_message_error(error)


@router.delete(
    "/{group_id}/messages/{message_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_message(
    group_id: UUID,
    message_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: RoomMessageService = Depends(get_room_message_service),
):
    _ensure_message_belongs_to_group(service, group_id, message_id)

    try:
        service.delete_message(
            message_id=message_id,
            user_id=user_id,
        )
    except ValueError as error:
        _raise_message_error(error)

    return Response(status_code=status.HTTP_204_NO_CONTENT)