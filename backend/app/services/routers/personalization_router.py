from uuid import UUID

from fastapi import APIRouter, Depends

from app.auth.jwt import get_current_user_id
from app.schemas.personalization_schema import (
    PersonalizationResponse,
    PersonalizationUpdate,
)
from app.services.dependencies import get_personalization_service
from app.services.personalization_service import PersonalizationService


router = APIRouter(
    prefix="/personalization",
    tags=["personalization"],
)


@router.put("")
def update_personalization(
    data: PersonalizationUpdate,
    user_id: UUID = Depends(get_current_user_id),
    service: PersonalizationService = Depends(
        get_personalization_service
    ),
):
    service.save_personalization(
        user_id=user_id,
        interests=data.interests,
        preferences=data.preferences,
        feature_preferences=data.feature_preferences,
        notification_enabled=data.notifications.enabled,
        daily_drop_enabled=data.notifications.daily_drop_enabled,
        group_activity_enabled=data.notifications.group_activity_enabled,
        quiet_hours_start=data.notifications.quiet_hours_start,
        quiet_hours_end=data.notifications.quiet_hours_end,
    )

    return {
        "message": "Personalization updated successfully",
    }


@router.get(
    "",
    response_model=PersonalizationResponse,
)
def get_personalization(
    user_id: UUID = Depends(get_current_user_id),
    service: PersonalizationService = Depends(
        get_personalization_service
    ),
):
    return service.get_personalization(user_id)