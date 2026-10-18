from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.auth.jwt import get_current_user_id
from app.schemas.mood_entry_schema import MoodEntryCreate, MoodEntryResponse
from app.services.dependencies import get_mood_entry_service
from app.services.mood_entry_service import (
    MoodEntryNotFoundError,
    MoodEntryService,
    MoodValidationError,
)

router = APIRouter(prefix="/moods", tags=["Moods"])


@router.post(
    "",
    response_model=MoodEntryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_mood_entry(
    payload: MoodEntryCreate,
    user_id: UUID = Depends(get_current_user_id),
    service: MoodEntryService = Depends(get_mood_entry_service),
):
    try:
        return service.create(
            user_id=user_id,
            mood=payload.mood,
            intensity=payload.intensity,
            note=payload.note,
        )
    except MoodValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.get("", response_model=list[MoodEntryResponse])
def list_mood_entries(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user_id: UUID = Depends(get_current_user_id),
    service: MoodEntryService = Depends(get_mood_entry_service),
):
    try:
        return service.list_for_user(
            user_id=user_id,
            limit=limit,
            offset=offset,
        )
    except MoodValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.get("/{entry_id}", response_model=MoodEntryResponse)
def get_mood_entry(
    entry_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: MoodEntryService = Depends(get_mood_entry_service),
):
    try:
        return service.get_for_user(user_id=user_id, entry_id=entry_id)
    except MoodEntryNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.delete(
    "/{entry_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_mood_entry(
    entry_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: MoodEntryService = Depends(get_mood_entry_service),
):
    try:
        service.delete(user_id=user_id, entry_id=entry_id)
    except MoodEntryNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)