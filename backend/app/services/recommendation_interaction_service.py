from uuid import UUID

from sqlalchemy.orm import Session

from app.models.recommendation_interaction import RecommendationInteraction
from app.repositories.recommendation_interaction_repository import (
    RecommendationInteractionRepository,
)
from app.repositories.recommendation_repository import RecommendationRepository


class RecommendationInteractionService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = RecommendationInteractionRepository(db)
        self.recommendation_repository = RecommendationRepository(db)

    def create_interaction(
        self,
        user_id: UUID,
        recommendation_id: UUID,
        interaction_type: str,
    ) -> RecommendationInteraction:
        if not interaction_type or not interaction_type.strip():
            raise ValueError("Interaction type cannot be empty")

        recommendation = self.recommendation_repository.get_by_id_for_user(
            recommendation_id=recommendation_id,
            user_id=user_id,
        )

        if recommendation is None:
            raise ValueError("Recommendation not found")

        interaction = self.repository.create(
            user_id=user_id,
            recommendation_id=recommendation_id,
            interaction_type=interaction_type,
        )

        self.db.commit()
        self.db.refresh(interaction)

        return interaction

    def get_interaction(
        self,
        interaction_id: UUID,
        user_id: UUID,
    ) -> RecommendationInteraction | None:
        return self.repository.get_by_id_for_user(
            interaction_id=interaction_id,
            user_id=user_id,
        )

    def get_user_interactions(
        self,
        user_id: UUID,
    ) -> list[RecommendationInteraction]:
        return self.repository.get_for_user(user_id)

    def get_recommendation_interactions(
        self,
        user_id: UUID,
        recommendation_id: UUID,
    ) -> list[RecommendationInteraction]:
        recommendation = self.recommendation_repository.get_by_id_for_user(
            recommendation_id=recommendation_id,
            user_id=user_id,
        )

        if recommendation is None:
            raise ValueError("Recommendation not found")

        return self.repository.get_for_recommendation(
            user_id=user_id,
            recommendation_id=recommendation_id,
        )

    def get_interactions_by_type(
        self,
        user_id: UUID,
        interaction_type: str,
    ) -> list[RecommendationInteraction]:
        if not interaction_type or not interaction_type.strip():
            raise ValueError("Interaction type cannot be empty")

        return self.repository.get_by_type_for_user(
            user_id=user_id,
            interaction_type=interaction_type,
        )

    def delete_interaction(
        self,
        interaction_id: UUID,
        user_id: UUID,
    ) -> bool:
        interaction = self.repository.get_by_id_for_user(
            interaction_id=interaction_id,
            user_id=user_id,
        )

        if interaction is None:
            raise ValueError("Interaction not found")

        deleted = self.repository.delete(
            interaction_id=interaction_id,
            user_id=user_id,
        )

        if deleted:
            self.db.commit()

        return deleted