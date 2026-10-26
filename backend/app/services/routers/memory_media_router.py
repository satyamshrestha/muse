from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.auth.jwt import get_current_user_id
from app.schemas.memory_media_schema import (
    MemoryMediaCreate,
    MemoryMediaRead,
)
from app.services.dependencies import get_memory_media_service
from app.services.memory_media_service import MemoryMediaService


router = APIRouter(prefix="/groups", tags=["memory-media"])


def _raise_memory_media_error(error: ValueError) -> None:
    message = str(error)
    lowered = message.lower()

    if "already attached" in lowered:
        code = status.HTTP_409_CONFLICT
    elif "not found" in lowered:
        code = status.HTTP_404_NOT_FOUND
    elif "limit must" in lowered or "offset cannot" in lowered:
        code = status.HTTP_422_UNPROCESSABLE_ENTITY
    else:
        code = status.HTTP_403_FORBIDDEN

    raise HTTPException(status_code=code, detail=message) from error


@router.post(
    "/{group_id}/memories/{memory_id}/media",
    response_model=MemoryMediaRead,
    status_code=status.HTTP_201_CREATED,
)
def attach_media(
    group_id: UUID,
    memory_id: UUID,
    payload: MemoryMediaCreate,
    user_id: UUID = Depends(get_current_user_id),
    service: MemoryMediaService = Depends(get_memory_media_service),
):
    try:
        return service.attach_media(
            group_id=group_id,
            memory_id=memory_id,
            media_id=payload.media_id,
            user_id=user_id,
        )
    except ValueError as error:
        _raise_memory_media_error(error)


@router.get(
    "/{group_id}/memories/{memory_id}/media",
    response_model=list[MemoryMediaRead],
)
def list_memory_media(
    group_id: UUID,
    memory_id: UUID,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user_id: UUID = Depends(get_current_user_id),
    service: MemoryMediaService = Depends(get_memory_media_service),
):
    try:
        return service.list_memory_media(
            group_id=group_id,
            memory_id=memory_id,
            user_id=user_id,
            limit=limit,
            offset=offset,
        )
    except ValueError as error:
        _raise_memory_media_error(error)


@router.delete(
    "/{group_id}/memories/{memory_id}/media/{link_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def detach_media(
    group_id: UUID,
    memory_id: UUID,
    link_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: MemoryMediaService = Depends(get_memory_media_service),
):
    try:
        service.detach_media(
            group_id=group_id,
            memory_id=memory_id,
            link_id=link_id,
            user_id=user_id,
        )
    except ValueError as error:
        _raise_memory_media_error(error)

    return Response(status_code=status.HTTP_204_NO_CONTENT)