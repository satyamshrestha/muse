from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.auth.jwt import get_current_user_id
from app.schemas.memory_schema import (
    MemoryCreate,
    MemoryRead,
    MemoryUpdate,
)
from app.services.dependencies import get_memory_service
from app.services.memory_service import MemoryService

router = APIRouter(prefix="/groups", tags=["memories"])


def _raise_memory_error(error: ValueError) -> None:
    message = str(error)

    if "not found" in message.lower():
        code = status.HTTP_404_NOT_FOUND
    elif "limit must" in message.lower() or "offset cannot" in message.lower():
        code = status.HTTP_422_UNPROCESSABLE_ENTITY
    else:
        code = status.HTTP_403_FORBIDDEN

    raise HTTPException(status_code=code, detail=message) from error


@router.post(
    "/{group_id}/memories",
    response_model=MemoryRead,
    status_code=status.HTTP_201_CREATED,
)
def create_memory(
    group_id: UUID,
    payload: MemoryCreate,
    user_id: UUID = Depends(get_current_user_id),
    service: MemoryService = Depends(get_memory_service),
):
    try:
        return service.create_memory(
            group_id=group_id,
            user_id=user_id,
            title=payload.title,
            description=payload.description,
            memory_date=payload.memory_date,
        )
    except ValueError as error:
        _raise_memory_error(error)


@router.get(
    "/{group_id}/memories",
    response_model=list[MemoryRead],
)
def list_memories(
    group_id: UUID,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user_id: UUID = Depends(get_current_user_id),
    service: MemoryService = Depends(get_memory_service),
):
    try:
        return service.list_memories(
            group_id=group_id,
            user_id=user_id,
            limit=limit,
            offset=offset,
        )
    except ValueError as error:
        _raise_memory_error(error)


@router.get(
    "/{group_id}/memories/{memory_id}",
    response_model=MemoryRead,
)
def get_memory(
    group_id: UUID,
    memory_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: MemoryService = Depends(get_memory_service),
):
    try:
        return service.get_memory(
            group_id=group_id,
            memory_id=memory_id,
            user_id=user_id,
        )
    except ValueError as error:
        _raise_memory_error(error)


@router.put(
    "/{group_id}/memories/{memory_id}",
    response_model=MemoryRead,
)
def update_memory(
    group_id: UUID,
    memory_id: UUID,
    payload: MemoryUpdate,
    user_id: UUID = Depends(get_current_user_id),
    service: MemoryService = Depends(get_memory_service),
):
    try:
        return service.update_memory(
            group_id=group_id,
            memory_id=memory_id,
            user_id=user_id,
            title=payload.title,
            description=payload.description,
            memory_date=payload.memory_date,
        )
    except ValueError as error:
        _raise_memory_error(error)


@router.delete(
    "/{group_id}/memories/{memory_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_memory(
    group_id: UUID,
    memory_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: MemoryService = Depends(get_memory_service),
):
    try:
        service.delete_memory(
            group_id=group_id,
            memory_id=memory_id,
            user_id=user_id,
        )
    except ValueError as error:
        _raise_memory_error(error)

    return Response(status_code=status.HTTP_204_NO_CONTENT)