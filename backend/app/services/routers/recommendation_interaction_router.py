from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.jwt import get_current_user_id
from app.schemas.recommendation_interaction_schema import (
    RecommendationInteractionCreate,
    RecommendationInteractionResponse,
)
from app.services.dependencies import (
    get_recommendation_interaction_service,
)
from app.services.recommendation_interaction_service import (
    RecommendationInteractionService,
)

router = APIRouter(
    prefix="/recommendation-interactions",
    tags=["Recommendation Interactions"],
)


@router.post(
    "",
    response_model=RecommendationInteractionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_recommendation_interaction(
    payload: RecommendationInteractionCreate,
    user_id: UUID = Depends(get_current_user_id),
    service: RecommendationInteractionService = Depends(
        get_recommendation_interaction_service
    ),
):
    try:
        return service.create_interaction(
            user_id=user_id,
            recommendation_id=payload.recommendation_id,
            interaction_type=payload.interaction_type,
        )
    except ValueError as exc:
        message = str(exc)

        if message == "Recommendation not found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=message,
            ) from exc

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=message,
        ) from exc


@router.get(
    "",
    response_model=list[RecommendationInteractionResponse],
)
def get_user_recommendation_interactions(
    user_id: UUID = Depends(get_current_user_id),
    service: RecommendationInteractionService = Depends(
        get_recommendation_interaction_service
    ),
):
    return service.get_user_interactions(user_id)


@router.get(
    "/recommendation/{recommendation_id}",
    response_model=list[RecommendationInteractionResponse],
)
def get_recommendation_interactions(
    recommendation_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: RecommendationInteractionService = Depends(
        get_recommendation_interaction_service
    ),
):
    try:
        return service.get_recommendation_interactions(
            user_id=user_id,
            recommendation_id=recommendation_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get(
    "/type/{interaction_type}",
    response_model=list[RecommendationInteractionResponse],
)
def get_interactions_by_type(
    interaction_type: str,
    user_id: UUID = Depends(get_current_user_id),
    service: RecommendationInteractionService = Depends(
        get_recommendation_interaction_service
    ),
):
    try:
        return service.get_interactions_by_type(
            user_id=user_id,
            interaction_type=interaction_type,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.get(
    "/{interaction_id}",
    response_model=RecommendationInteractionResponse,
)
def get_recommendation_interaction(
    interaction_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: RecommendationInteractionService = Depends(
        get_recommendation_interaction_service
    ),
):
    interaction = service.get_interaction(
        interaction_id=interaction_id,
        user_id=user_id,
    )

    if interaction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interaction not found",
        )

    return interaction


@router.delete(
    "/{interaction_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_recommendation_interaction(
    interaction_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: RecommendationInteractionService = Depends(
        get_recommendation_interaction_service
    ),
):
    try:
        service.delete_interaction(
            interaction_id=interaction_id,
            user_id=user_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return None