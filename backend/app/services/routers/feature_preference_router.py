from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.jwt import get_current_user_id
from app.schemas.feature_preference_schema import (
    FeaturePreferenceItem,
    FeaturePreferenceReplace,
    FeaturePreferenceResponse,
)
from app.services.dependencies import get_feature_preference_service
from app.services.feature_preference_service import (
    FeaturePreferenceService,
    FeaturePreferenceValidationError,
)

router = APIRouter(
    prefix="/feature-preferences",
    tags=["Feature Preferences"],
)


@router.get("", response_model=FeaturePreferenceResponse)
def get_feature_preferences(
    user_id: UUID = Depends(get_current_user_id),
    service: FeaturePreferenceService = Depends(
        get_feature_preference_service
    ),
):
    return FeaturePreferenceResponse(
        feature_preferences=[
            FeaturePreferenceItem.model_validate(record)
            for record in service.get_for_user(user_id)
        ]
    )


@router.put("", response_model=FeaturePreferenceResponse)
def replace_feature_preferences(
    payload: FeaturePreferenceReplace,
    user_id: UUID = Depends(get_current_user_id),
    service: FeaturePreferenceService = Depends(
        get_feature_preference_service
    ),
):
    try:
        records = service.replace_for_user(
            user_id,
            payload.feature_preferences,
        )
    except FeaturePreferenceValidationError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error

    return FeaturePreferenceResponse(
        feature_preferences=[
            FeaturePreferenceItem.model_validate(record)
            for record in records
        ]
    )