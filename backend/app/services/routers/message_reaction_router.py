from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select

from app.auth.jwt import get_current_user_id
from app.models.room_message import RoomMessage
from app.schemas.message_reaction_schema import (
    MessageReactionCreate,
    MessageReactionRead,
    MessageReactionUpdate,
)
from app.services.dependencies import get_message_reaction_service
from app.services.message_reaction_service import MessageReactionService


router = APIRouter(
    prefix="/groups",
    tags=["message-reactions"],
)


def _ensure_message_belongs_to_group(
    service: MessageReactionService,
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


def _raise_reaction_error(error: ValueError) -> None:
    message = str(error)
    lowered = message.lower()

    if "not found" in lowered:
        code = status.HTTP_404_NOT_FOUND
    elif "already reacted" in lowered:
        code = status.HTTP_409_CONFLICT
    elif "must not be empty" in lowered:
        code = status.HTTP_422_UNPROCESSABLE_ENTITY
    else:
        code = status.HTTP_403_FORBIDDEN

    raise HTTPException(
        status_code=code,
        detail=message,
    ) from error


@router.post(
    "/{group_id}/messages/{message_id}/reactions",
    response_model=MessageReactionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_reaction(
    group_id: UUID,
    message_id: UUID,
    payload: MessageReactionCreate,
    user_id: UUID = Depends(get_current_user_id),
    service: MessageReactionService = Depends(
        get_message_reaction_service
    ),
):
    _ensure_message_belongs_to_group(service, group_id, message_id)

    try:
        return service.create_reaction(
            message_id=message_id,
            user_id=user_id,
            reaction=payload.reaction,
        )
    except ValueError as error:
        _raise_reaction_error(error)


@router.get(
    "/{group_id}/messages/{message_id}/reactions",
    response_model=list[MessageReactionRead],
)
def list_reactions(
    group_id: UUID,
    message_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: MessageReactionService = Depends(
        get_message_reaction_service
    ),
):
    _ensure_message_belongs_to_group(service, group_id, message_id)

    try:
        return service.get_message_reactions(
            message_id=message_id,
            user_id=user_id,
        )
    except ValueError as error:
        _raise_reaction_error(error)


@router.put(
    "/{group_id}/messages/{message_id}/reactions/{reaction_id}",
    response_model=MessageReactionRead,
)
def update_reaction(
    group_id: UUID,
    message_id: UUID,
    reaction_id: UUID,
    payload: MessageReactionUpdate,
    user_id: UUID = Depends(get_current_user_id),
    service: MessageReactionService = Depends(
        get_message_reaction_service
    ),
):
    _ensure_message_belongs_to_group(service, group_id, message_id)

    reaction = service.reaction_repository.get_by_id(reaction_id)
    if reaction is None or reaction.message_id != message_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message reaction not found",
        )

    try:
        return service.update_reaction(
            reaction_id=reaction_id,
            user_id=user_id,
            reaction=payload.reaction,
        )
    except ValueError as error:
        _raise_reaction_error(error)


@router.delete(
    "/{group_id}/messages/{message_id}/reactions/{reaction_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_reaction(
    group_id: UUID,
    message_id: UUID,
    reaction_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: MessageReactionService = Depends(
        get_message_reaction_service
    ),
):
    _ensure_message_belongs_to_group(service, group_id, message_id)

    reaction = service.reaction_repository.get_by_id(reaction_id)
    if reaction is None or reaction.message_id != message_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message reaction not found",
        )

    try:
        service.delete_reaction(
            reaction_id=reaction_id,
            user_id=user_id,
        )
    except ValueError as error:
        _raise_reaction_error(error)

    return Response(status_code=status.HTTP_204_NO_CONTENT)