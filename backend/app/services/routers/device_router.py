from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.auth.jwt import get_current_user_id
from app.schemas.device_schema import (
    DevicePlatformUpdate,
    DeviceRegisterRequest,
    DeviceResponse,
)
from app.services.dependencies import get_device_service
from app.services.device_service import (
    DeviceNotFoundError,
    DeviceService,
    DeviceTokenConflictError,
)

router = APIRouter(prefix="/devices", tags=["devices"])


@router.post(
    "",
    response_model=DeviceResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_device(
    data: DeviceRegisterRequest,
    user_id: UUID = Depends(get_current_user_id),
    service: DeviceService = Depends(get_device_service),
):
    try:
        return service.register(
            user_id=user_id,
            device_token=data.device_token,
            platform=data.platform,
        )
    except DeviceTokenConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.get("", response_model=list[DeviceResponse])
def list_devices(
    user_id: UUID = Depends(get_current_user_id),
    service: DeviceService = Depends(get_device_service),
):
    return service.list_for_user(user_id)


@router.patch("/{device_id}", response_model=DeviceResponse)
def update_device_platform(
    device_id: UUID,
    data: DevicePlatformUpdate,
    user_id: UUID = Depends(get_current_user_id),
    service: DeviceService = Depends(get_device_service),
):
    try:
        return service.update_platform(
            user_id=user_id,
            device_id=device_id,
            platform=data.platform,
        )
    except DeviceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.delete(
    "/{device_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def unregister_device(
    device_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: DeviceService = Depends(get_device_service),
):
    try:
        service.unregister(
            user_id=user_id,
            device_id=device_id,
        )
    except DeviceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)