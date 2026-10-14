from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth.jwt import get_current_user_id
from app.schemas.notification_schema import (
    MarkAllReadResponse,
    NotificationListResponse,
    NotificationResponse,
    UnreadCountResponse,
)
from app.services.dependencies import get_notification_service
from app.services.notification_service import (
    NotificationNotFoundError,
    NotificationService,
)

router = APIRouter(
    prefix="/notifications",
    tags=["notifications"],
)


@router.get("", response_model=NotificationListResponse)
def list_notifications(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    unread_only: bool = False,
    user_id: UUID = Depends(get_current_user_id),
    service: NotificationService = Depends(get_notification_service),
):
    items = service.list_for_user(
        user_id=user_id,
        limit=limit,
        offset=offset,
        unread_only=unread_only,
    )
    return NotificationListResponse(
        items=items,
        limit=limit,
        offset=offset,
    )


@router.get("/unread-count", response_model=UnreadCountResponse)
def get_unread_count(
    user_id: UUID = Depends(get_current_user_id),
    service: NotificationService = Depends(get_notification_service),
):
    return UnreadCountResponse(
        unread_count=service.unread_count(user_id)
    )


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_read(
    notification_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: NotificationService = Depends(get_notification_service),
):
    try:
        return service.mark_read(
            user_id=user_id,
            notification_id=notification_id,
        )
    except NotificationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.post("/read-all", response_model=MarkAllReadResponse)
def mark_all_notifications_read(
    user_id: UUID = Depends(get_current_user_id),
    service: NotificationService = Depends(get_notification_service),
):
    return MarkAllReadResponse(
        updated_count=service.mark_all_read(user_id)
    )