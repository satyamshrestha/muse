from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.auth.jwt import get_current_user_id
from app.schemas.group_recommendation_schema import (
    GroupRecommendationCreate,
    GroupRecommendationRead,
)
from app.services.dependencies import get_group_recommendation_service
from app.services.group_recommendation_service import (
    GroupRecommendationService,
)


router = APIRouter(prefix="/groups", tags=["group-recommendations"])


def _raise_recommendation_error(error: ValueError) -> None:
    message = str(error)

    if "not found" in message.lower():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=message,
        ) from error

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=message,
    ) from error


@router.post(
    "/{group_id}/recommendations",
    response_model=GroupRecommendationRead,
    status_code=status.HTTP_201_CREATED,
)
def create_recommendation(
    group_id: UUID,
    payload: GroupRecommendationCreate,
    user_id: UUID = Depends(get_current_user_id),
    service: GroupRecommendationService = Depends(
        get_group_recommendation_service
    ),
):
    try:
        return service.create_recommendation_for_user(
            group_id=group_id,
            user_id=user_id,
            recommendation_type=payload.recommendation_type,
            title=payload.title,
            description=payload.description,
        )
    except ValueError as error:
        _raise_recommendation_error(error)


@router.get(
    "/{group_id}/recommendations",
    response_model=list[GroupRecommendationRead],
)
def get_group_recommendations(
    group_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: GroupRecommendationService = Depends(
        get_group_recommendation_service
    ),
):
    try:
        return service.get_group_recommendations_for_user(
            group_id,
            user_id,
        )
    except ValueError as error:
        _raise_recommendation_error(error)


@router.get(
    "/{group_id}/recommendations/type/{recommendation_type}",
    response_model=list[GroupRecommendationRead],
)
def get_recommendations_by_type(
    group_id: UUID,
    recommendation_type: str,
    user_id: UUID = Depends(get_current_user_id),
    service: GroupRecommendationService = Depends(
        get_group_recommendation_service
    ),
):
    try:
        return service.get_recommendations_by_type_for_user(
            group_id=group_id,
            user_id=user_id,
            recommendation_type=recommendation_type,
        )
    except ValueError as error:
        _raise_recommendation_error(error)


@router.get(
    "/{group_id}/recommendations/{recommendation_id}",
    response_model=GroupRecommendationRead,
)
def get_recommendation(
    group_id: UUID,
    recommendation_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: GroupRecommendationService = Depends(
        get_group_recommendation_service
    ),
):
    try:
        recommendation = service.get_recommendation_for_user(
            recommendation_id,
            user_id,
        )
    except ValueError as error:
        _raise_recommendation_error(error)

    if recommendation.group_id != group_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group recommendation not found",
        )

    return recommendation


@router.delete(
    "/{group_id}/recommendations/{recommendation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_recommendation(
    group_id: UUID,
    recommendation_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: GroupRecommendationService = Depends(
        get_group_recommendation_service
    ),
):
    try:
        recommendation = service.get_recommendation_for_user(
            recommendation_id,
            user_id,
        )

        if recommendation.group_id != group_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Group recommendation not found",
            )

        service.delete_recommendation_for_user(
            recommendation_id,
            user_id,
        )
    except ValueError as error:
        _raise_recommendation_error(error)

    return Response(status_code=status.HTTP_204_NO_CONTENT)