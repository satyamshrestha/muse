from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.recommendation import Recommendation


class RecommendationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        user_id: UUID,
        recommendation_type: str,
        title: str,
        source: str,
        description: str | None = None,
    ) -> Recommendation:
        recommendation = Recommendation(
            user_id=user_id,
            recommendation_type=recommendation_type,
            title=title,
            description=description,
            source=source,
        )
        self.db.add(recommendation)
        self.db.flush()
        return recommendation

    def get_by_id_for_user(
        self,
        recommendation_id: UUID,
        user_id: UUID,
    ) -> Recommendation | None:
        statement = select(Recommendation).where(
            Recommendation.id == recommendation_id,
            Recommendation.user_id == user_id,
        )
        return self.db.scalar(statement)

    def get_for_user(
        self,
        user_id: UUID,
    ) -> list[Recommendation]:
        statement = (
            select(Recommendation)
            .where(Recommendation.user_id == user_id)
            .order_by(
                Recommendation.created_at.desc(),
                Recommendation.id.desc(),
            )
        )
        return list(self.db.scalars(statement).all())

    def get_by_type_for_user(
        self,
        user_id: UUID,
        recommendation_type: str,
    ) -> list[Recommendation]:
        statement = (
            select(Recommendation)
            .where(
                Recommendation.user_id == user_id,
                Recommendation.recommendation_type == recommendation_type,
            )
            .order_by(
                Recommendation.created_at.desc(),
                Recommendation.id.desc(),
            )
        )
        return list(self.db.scalars(statement).all())

    def get_by_source_for_user(
        self,
        user_id: UUID,
        source: str,
    ) -> list[Recommendation]:
        statement = (
            select(Recommendation)
            .where(
                Recommendation.user_id == user_id,
                Recommendation.source == source,
            )
            .order_by(
                Recommendation.created_at.desc(),
                Recommendation.id.desc(),
            )
        )
        return list(self.db.scalars(statement).all())

    def delete(self, recommendation_id: UUID) -> bool:
        result = self.db.execute(
            delete(Recommendation).where(
                Recommendation.id == recommendation_id
            )
        )
        self.db.flush()
        return result.rowcount > 0