from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.exc import IntegrityError

from app.auth.jwt import get_current_user_id
from app.schemas.media_schema import MediaCreate, MediaRead
from app.services.dependencies import get_media_service
from app.services.media_service import MediaService


router = APIRouter(prefix="/media", tags=["media"])


def _raise_media_error(error: ValueError) -> None:
    message = str(error)
    lowered = message.lower()

    if "not found" in lowered:
        code = status.HTTP_404_NOT_FOUND
    elif "limit must" in lowered or "offset cannot" in lowered:
        code = status.HTTP_422_UNPROCESSABLE_ENTITY
    elif "cannot be empty" in lowered or "cannot exceed" in lowered:
        code = status.HTTP_422_UNPROCESSABLE_ENTITY
    elif "already attached" in lowered:
        code = status.HTTP_409_CONFLICT
    else:
        code = status.HTTP_403_FORBIDDEN

    raise HTTPException(status_code=code, detail=message) from error


@router.post(
    "",
    response_model=MediaRead,
    status_code=status.HTTP_201_CREATED,
)
def register_media(
    payload: MediaCreate,
    user_id: UUID = Depends(get_current_user_id),
    service: MediaService = Depends(get_media_service),
):
    try:
        return service.register_media(
            user_id=user_id,
            object_key=payload.object_key,
            media_type=payload.media_type,
            mime_type=payload.mime_type,
        )
    except IntegrityError as error:
        service.db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Media object key already exists",
        ) from error
    except ValueError as error:
        _raise_media_error(error)


@router.get("", response_model=list[MediaRead])
def list_media(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user_id: UUID = Depends(get_current_user_id),
    service: MediaService = Depends(get_media_service),
):
    try:
        return service.list_media(
            user_id=user_id,
            limit=limit,
            offset=offset,
        )
    except ValueError as error:
        _raise_media_error(error)


@router.get("/{media_id}", response_model=MediaRead)
def get_media(
    media_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: MediaService = Depends(get_media_service),
):
    try:
        return service.get_media(
            media_id=media_id,
            user_id=user_id,
        )
    except ValueError as error:
        _raise_media_error(error)


@router.delete(
    "/{media_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_media(
    media_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: MediaService = Depends(get_media_service),
):
    try:
        service.delete_media(
            media_id=media_id,
            user_id=user_id,
        )
    except ValueError as error:
        _raise_media_error(error)

    return Response(status_code=status.HTTP_204_NO_CONTENT)