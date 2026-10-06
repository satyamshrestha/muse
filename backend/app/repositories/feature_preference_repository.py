from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.feature_preference import FeaturePreference


class FeaturePreferenceRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_user_id(
        self,
        user_id: UUID,
    ) -> list[FeaturePreference]:
        return list(
            self.db.scalars(
                select(FeaturePreference).where(
                    FeaturePreference.user_id == user_id
                )
            )
        )

    def replace_for_user(
        self,
        user_id: UUID,
        feature_preferences: dict[str, str],
    ) -> list[FeaturePreference]:
        self.db.execute(
            delete(FeaturePreference).where(
                FeaturePreference.user_id == user_id
            )
        )

        records = [
            FeaturePreference(
                user_id=user_id,
                feature=feature,
                preference=preference,
            )
            for feature, preference in feature_preferences.items()
        ]

        self.db.add_all(records)
        self.db.flush()

        return records