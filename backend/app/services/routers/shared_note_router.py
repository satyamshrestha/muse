from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.auth.jwt import get_current_user_id
from app.schemas.shared_note_schema import (
    SharedNoteCreate,
    SharedNoteRead,
    SharedNoteUpdate,
)
from app.services.dependencies import get_shared_note_service
from app.services.shared_note_service import SharedNoteService

router = APIRouter(prefix="/groups", tags=["shared-notes"])


def _raise_shared_note_error(error: ValueError) -> None:
    message = str(error)

    if "not found" in message.lower():
        code = status.HTTP_404_NOT_FOUND
    elif "limit must" in message.lower() or "offset cannot" in message.lower():
        code = status.HTTP_422_UNPROCESSABLE_ENTITY
    else:
        code = status.HTTP_403_FORBIDDEN

    raise HTTPException(status_code=code, detail=message) from error


@router.post(
    "/{group_id}/shared-notes",
    response_model=SharedNoteRead,
    status_code=status.HTTP_201_CREATED,
)
def create_shared_note(
    group_id: UUID,
    payload: SharedNoteCreate,
    user_id: UUID = Depends(get_current_user_id),
    service: SharedNoteService = Depends(get_shared_note_service),
):
    try:
        return service.create_note(
            group_id=group_id,
            user_id=user_id,
            title=payload.title,
            content=payload.content,
        )
    except ValueError as error:
        _raise_shared_note_error(error)


@router.get(
    "/{group_id}/shared-notes",
    response_model=list[SharedNoteRead],
)
def list_shared_notes(
    group_id: UUID,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user_id: UUID = Depends(get_current_user_id),
    service: SharedNoteService = Depends(get_shared_note_service),
):
    try:
        return service.list_notes(
            group_id=group_id,
            user_id=user_id,
            limit=limit,
            offset=offset,
        )
    except ValueError as error:
        _raise_shared_note_error(error)


@router.get(
    "/{group_id}/shared-notes/{note_id}",
    response_model=SharedNoteRead,
)
def get_shared_note(
    group_id: UUID,
    note_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: SharedNoteService = Depends(get_shared_note_service),
):
    try:
        return service.get_note(
            group_id=group_id,
            note_id=note_id,
            user_id=user_id,
        )
    except ValueError as error:
        _raise_shared_note_error(error)


@router.put(
    "/{group_id}/shared-notes/{note_id}",
    response_model=SharedNoteRead,
)
def update_shared_note(
    group_id: UUID,
    note_id: UUID,
    payload: SharedNoteUpdate,
    user_id: UUID = Depends(get_current_user_id),
    service: SharedNoteService = Depends(get_shared_note_service),
):
    try:
        return service.update_note(
            group_id=group_id,
            note_id=note_id,
            user_id=user_id,
            title=payload.title,
            content=payload.content,
        )
    except ValueError as error:
        _raise_shared_note_error(error)


@router.delete(
    "/{group_id}/shared-notes/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_shared_note(
    group_id: UUID,
    note_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: SharedNoteService = Depends(get_shared_note_service),
):
    try:
        service.delete_note(
            group_id=group_id,
            note_id=note_id,
            user_id=user_id,
        )
    except ValueError as error:
        _raise_shared_note_error(error)

    return Response(status_code=status.HTTP_204_NO_CONTENT)