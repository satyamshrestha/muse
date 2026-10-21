from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.jwt import get_current_user_id
from app.schemas.notification_preference_schema import (
    NotificationPreferenceResponse,
    NotificationPreferenceUpdate,
)
from app.services.dependencies import get_notification_preference_service
from app.services.notification_preference_service import (
    NotificationPreferenceService,
)
from app.services.notification_service import NotificationPreferenceError

router = APIRouter(
    prefix="/notification-preferences",
    tags=["Notification Preferences"],
)


@router.get(
    "",
    response_model=NotificationPreferenceResponse | None,
)
def get_notification_preferences(
    user_id: UUID = Depends(get_current_user_id),
    service: NotificationPreferenceService = Depends(
        get_notification_preference_service
    ),
):
    return service.get_for_user(user_id)


@router.put(
    "",
    response_model=NotificationPreferenceResponse,
)
def update_notification_preferences(
    payload: NotificationPreferenceUpdate,
    user_id: UUID = Depends(get_current_user_id),
    service: NotificationPreferenceService = Depends(
        get_notification_preference_service
    ),
):
    try:
        return service.update_for_user(
            user_id=user_id,
            enabled=payload.enabled,
            daily_drop_enabled=payload.daily_drop_enabled,
            group_activity_enabled=payload.group_activity_enabled,
            quiet_hours_start=payload.quiet_hours_start,
            quiet_hours_end=payload.quiet_hours_end,
        )
    except NotificationPreferenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc