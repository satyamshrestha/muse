from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.auth.jwt import get_current_user_id
from app.schemas.personal_note_schema import (
    PersonalNoteCreate,
    PersonalNoteResponse,
    PersonalNoteUpdate,
)
from app.services.dependencies import get_personal_note_service
from app.services.personal_note_service import (
    PersonalNoteNotFoundError,
    PersonalNoteService,
    PersonalNoteValidationError,
)

router = APIRouter(prefix="/notes", tags=["Personal Notes"])


@router.post(
    "",
    response_model=PersonalNoteResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_personal_note(
    payload: PersonalNoteCreate,
    user_id: UUID = Depends(get_current_user_id),
    service: PersonalNoteService = Depends(get_personal_note_service),
):
    try:
        return service.create(
            user_id=user_id,
            title=payload.title,
            content=payload.content,
        )
    except PersonalNoteValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.get("", response_model=list[PersonalNoteResponse])
def list_personal_notes(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user_id: UUID = Depends(get_current_user_id),
    service: PersonalNoteService = Depends(get_personal_note_service),
):
    try:
        return service.list_for_user(
            user_id=user_id,
            limit=limit,
            offset=offset,
        )
    except PersonalNoteValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.get("/{note_id}", response_model=PersonalNoteResponse)
def get_personal_note(
    note_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: PersonalNoteService = Depends(get_personal_note_service),
):
    try:
        return service.get_for_user(user_id=user_id, note_id=note_id)
    except PersonalNoteNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.put("/{note_id}", response_model=PersonalNoteResponse)
def update_personal_note(
    note_id: UUID,
    payload: PersonalNoteUpdate,
    user_id: UUID = Depends(get_current_user_id),
    service: PersonalNoteService = Depends(get_personal_note_service),
):
    try:
        return service.update(
            user_id=user_id,
            note_id=note_id,
            title=payload.title,
            content=payload.content,
        )
    except PersonalNoteNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except PersonalNoteValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.delete(
    "/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_personal_note(
    note_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: PersonalNoteService = Depends(get_personal_note_service),
):
    try:
        service.delete(user_id=user_id, note_id=note_id)
    except PersonalNoteNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)