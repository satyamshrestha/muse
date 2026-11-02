from uuid import UUID

from sqlalchemy.orm import Session

from app.models.group_recommendation import GroupRecommendation
from app.repositories.group_recommendation_repository import (
    GroupRecommendationRepository,
)


class GroupRecommendationService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = GroupRecommendationRepository(db)

    def create_recommendation(
        self,
        group_id: UUID,
        created_by: UUID,
        recommendation_type: str,
        title: str,
        description: str | None = None,
    ) -> GroupRecommendation:
        if not recommendation_type or not recommendation_type.strip():
            raise ValueError("Recommendation type cannot be empty")

        if not title or not title.strip():
            raise ValueError("Title cannot be empty")

        if description is not None and not description.strip():
            raise ValueError("Description cannot be empty")

        recommendation = self.repository.create(
            group_id=group_id,
            created_by=created_by,
            recommendation_type=recommendation_type,
            title=title,
            description=description,
        )

        self.db.commit()
        self.db.refresh(recommendation)

        return recommendation

    def get_recommendation(
        self,
        recommendation_id: UUID,
    ) -> GroupRecommendation | None:
        return self.repository.get_by_id(recommendation_id)

    def get_group_recommendations(
        self,
        group_id: UUID,
    ) -> list[GroupRecommendation]:
        return self.repository.get_for_group(group_id)

    def get_recommendations_by_type(
        self,
        group_id: UUID,
        recommendation_type: str,
    ) -> list[GroupRecommendation]:
        if not recommendation_type or not recommendation_type.strip():
            raise ValueError("Recommendation type cannot be empty")

        return self.repository.get_by_type(group_id, recommendation_type)

    def delete_recommendation(
        self,
        recommendation_id: UUID,
    ) -> bool:
        recommendation = self.repository.get_by_id(recommendation_id)

        if recommendation is None:
            raise ValueError("Group recommendation not found")

        self.repository.delete(recommendation_id)
        self.db.commit()

        return True