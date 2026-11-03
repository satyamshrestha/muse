from uuid import UUID

from sqlalchemy.orm import Session

from app.models.recommendation import Recommendation
from app.repositories.recommendation_repository import (
    RecommendationRepository,
)


class RecommendationService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = RecommendationRepository(db)

    def create_recommendation(
        self,
        user_id: UUID,
        recommendation_type: str,
        title: str,
        source: str,
        description: str | None = None,
    ) -> Recommendation:
        if not recommendation_type or not recommendation_type.strip():
            raise ValueError("Recommendation type cannot be empty")

        if not title or not title.strip():
            raise ValueError("Title cannot be empty")

        if not source or not source.strip():
            raise ValueError("Source cannot be empty")

        if description is not None and not description.strip():
            raise ValueError("Description cannot be empty")

        recommendation = self.repository.create(
            user_id=user_id,
            recommendation_type=recommendation_type,
            title=title,
            description=description,
            source=source,
        )

        self.db.commit()
        self.db.refresh(recommendation)

        return recommendation

    def get_recommendation(
        self,
        recommendation_id: UUID,
        user_id: UUID,
    ) -> Recommendation | None:
        return self.repository.get_by_id_for_user(
            recommendation_id,
            user_id,
        )

    def get_user_recommendations(
        self,
        user_id: UUID,
    ) -> list[Recommendation]:
        return self.repository.get_for_user(user_id)

    def get_recommendations_by_type(
        self,
        user_id: UUID,
        recommendation_type: str,
    ) -> list[Recommendation]:
        if not recommendation_type or not recommendation_type.strip():
            raise ValueError("Recommendation type cannot be empty")

        return self.repository.get_by_type_for_user(
            user_id,
            recommendation_type,
        )

    def get_recommendations_by_source(
        self,
        user_id: UUID,
        source: str,
    ) -> list[Recommendation]:
        if not source or not source.strip():
            raise ValueError("Source cannot be empty")

        return self.repository.get_by_source_for_user(
            user_id,
            source,
        )

    def delete_recommendation(
        self,
        recommendation_id: UUID,
        user_id: UUID,
    ) -> bool:
        recommendation = self.repository.get_by_id_for_user(
            recommendation_id,
            user_id,
        )

        if recommendation is None:
            raise ValueError("Recommendation not found")

        deleted = self.repository.delete(recommendation_id)

        if deleted:
            self.db.commit()

        return deleted