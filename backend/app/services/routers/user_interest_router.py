from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.jwt import get_current_user_id
from app.schemas.user_interest_schema import (
    UserInterestItem,
    UserInterestReplace,
    UserInterestResponse,
)
from app.services.dependencies import get_user_interest_service
from app.services.user_interest_service import (
    UserInterestService,
    UserInterestValidationError,
)

router = APIRouter(prefix="/interests", tags=["Interests"])


@router.get("", response_model=UserInterestResponse)
def get_interests(
    user_id: UUID = Depends(get_current_user_id),
    service: UserInterestService = Depends(get_user_interest_service),
):
    return UserInterestResponse(
        interests=[
            UserInterestItem.model_validate(record)
            for record in service.get_for_user(user_id)
        ]
    )


@router.put("", response_model=UserInterestResponse)
def replace_interests(
    payload: UserInterestReplace,
    user_id: UUID = Depends(get_current_user_id),
    service: UserInterestService = Depends(get_user_interest_service),
):
    try:
        records = service.replace_for_user(
            user_id,
            payload.interests,
        )
    except UserInterestValidationError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error

    return UserInterestResponse(
        interests=[
            UserInterestItem.model_validate(record)
            for record in records
        ]
    )