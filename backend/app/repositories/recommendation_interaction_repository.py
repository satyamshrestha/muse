from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.recommendation_interaction import RecommendationInteraction


class RecommendationInteractionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        user_id: UUID,
        recommendation_id: UUID,
        interaction_type: str,
    ) -> RecommendationInteraction:
        interaction = RecommendationInteraction(
            user_id=user_id,
            recommendation_id=recommendation_id,
            interaction_type=interaction_type,
        )
        self.db.add(interaction)
        self.db.flush()
        return interaction

    def get_by_id_for_user(
        self,
        interaction_id: UUID,
        user_id: UUID,
    ) -> RecommendationInteraction | None:
        statement = select(RecommendationInteraction).where(
            RecommendationInteraction.id == interaction_id,
            RecommendationInteraction.user_id == user_id,
        )
        return self.db.scalar(statement)

    def get_for_user(
        self,
        user_id: UUID,
    ) -> list[RecommendationInteraction]:
        statement = (
            select(RecommendationInteraction)
            .where(RecommendationInteraction.user_id == user_id)
            .order_by(
                RecommendationInteraction.created_at.desc(),
                RecommendationInteraction.id.desc(),
            )
        )
        return list(self.db.scalars(statement).all())

    def get_for_recommendation(
        self,
        user_id: UUID,
        recommendation_id: UUID,
    ) -> list[RecommendationInteraction]:
        statement = (
            select(RecommendationInteraction)
            .where(
                RecommendationInteraction.user_id == user_id,
                RecommendationInteraction.recommendation_id == recommendation_id,
            )
            .order_by(
                RecommendationInteraction.created_at.desc(),
                RecommendationInteraction.id.desc(),
            )
        )
        return list(self.db.scalars(statement).all())

    def get_by_type_for_user(
        self,
        user_id: UUID,
        interaction_type: str,
    ) -> list[RecommendationInteraction]:
        statement = (
            select(RecommendationInteraction)
            .where(
                RecommendationInteraction.user_id == user_id,
                RecommendationInteraction.interaction_type == interaction_type,
            )
            .order_by(
                RecommendationInteraction.created_at.desc(),
                RecommendationInteraction.id.desc(),
            )
        )
        return list(self.db.scalars(statement).all())

    def delete(
        self,
        interaction_id: UUID,
        user_id: UUID,
    ) -> bool:
        result = self.db.execute(
            delete(RecommendationInteraction).where(
                RecommendationInteraction.id == interaction_id,
                RecommendationInteraction.user_id == user_id,
            )
        )
        self.db.flush()
        return result.rowcount > 0