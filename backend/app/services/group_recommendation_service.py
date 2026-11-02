from uuid import UUID

from sqlalchemy.orm import Session

from app.models.group_recommendation import GroupRecommendation
from app.repositories.group_recommendation_repository import GroupRecommendationRepository
from app.repositories.friend_group_repository import FriendGroupRepository
from app.repositories.group_membership_repository import GroupMembershipRepository


class GroupRecommendationService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = GroupRecommendationRepository(db)
        self.group_repository = FriendGroupRepository(db)
        self.membership_repository = GroupMembershipRepository(db)


    def _ensure_group_member(self, group_id: UUID, user_id: UUID) -> None:
        group = self.group_repository.get_by_id(group_id)

        if group is None:
            raise ValueError("Group not found")

        if not self.membership_repository.is_member(user_id, group_id):
            raise ValueError("User is not a member of this group")

    def create_recommendation_for_user(
        self,
        group_id: UUID,
        user_id: UUID,
        recommendation_type: str,
        title: str,
        description: str | None = None,
    ) -> GroupRecommendation:
        self._ensure_group_member(group_id, user_id)

        return self.create_recommendation(
            group_id=group_id,
            created_by=user_id,
            recommendation_type=recommendation_type,
            title=title,
            description=description,
        )

    def get_group_recommendations_for_user(
        self,
        group_id: UUID,
        user_id: UUID,
    ) -> list[GroupRecommendation]:
        self._ensure_group_member(group_id, user_id)
        return self.get_group_recommendations(group_id)

    def get_recommendations_by_type_for_user(
        self,
        group_id: UUID,
        user_id: UUID,
        recommendation_type: str,
    ) -> list[GroupRecommendation]:
        self._ensure_group_member(group_id, user_id)

        return self.get_recommendations_by_type(
            group_id,
            recommendation_type,
        )

    def get_recommendation_for_user(
        self,
        recommendation_id: UUID,
        user_id: UUID,
    ) -> GroupRecommendation:
        recommendation = self.get_recommendation(recommendation_id)

        if recommendation is None:
            raise ValueError("Group recommendation not found")

        self._ensure_group_member(recommendation.group_id, user_id)
        return recommendation

    def delete_recommendation_for_user(
        self,
        recommendation_id: UUID,
        user_id: UUID,
    ) -> bool:
        recommendation = self.get_recommendation_for_user(
            recommendation_id,
            user_id,
        )

        if recommendation.created_by != user_id:
            raise ValueError(
                "Only the recommendation creator can delete it"
            )

        return self.delete_recommendation(recommendation_id)

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