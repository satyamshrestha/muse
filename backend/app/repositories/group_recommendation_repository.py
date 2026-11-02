from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.group_recommendation import GroupRecommendation


class GroupRecommendationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        group_id: UUID,
        created_by: UUID,
        recommendation_type: str,
        title: str,
        description: str | None = None,
    ) -> GroupRecommendation:
        recommendation = GroupRecommendation(
            group_id=group_id,
            created_by=created_by,
            recommendation_type=recommendation_type,
            title=title,
            description=description,
        )
        self.db.add(recommendation)
        self.db.flush()
        return recommendation

    def get_by_id(
        self,
        recommendation_id: UUID,
    ) -> GroupRecommendation | None:
        return self.db.scalar(
            select(GroupRecommendation).where(
                GroupRecommendation.id == recommendation_id
            )
        )

    def get_for_group(
        self,
        group_id: UUID,
    ) -> list[GroupRecommendation]:
        statement = (
            select(GroupRecommendation)
            .where(GroupRecommendation.group_id == group_id)
            .order_by(GroupRecommendation.created_at.desc())
        )
        return list(self.db.scalars(statement))

    def get_by_type(
        self,
        group_id: UUID,
        recommendation_type: str,
    ) -> list[GroupRecommendation]:
        statement = (
            select(GroupRecommendation)
            .where(
                GroupRecommendation.group_id == group_id,
                GroupRecommendation.recommendation_type == recommendation_type,
            )
            .order_by(GroupRecommendation.created_at.desc())
        )
        return list(self.db.scalars(statement))

    def delete(self, recommendation_id: UUID) -> bool:
        result = self.db.execute(
            delete(GroupRecommendation).where(
                GroupRecommendation.id == recommendation_id
            )
        )
        self.db.flush()
        return result.rowcount > 0