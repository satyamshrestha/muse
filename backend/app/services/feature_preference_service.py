from uuid import UUID

from sqlalchemy.orm import Session

from app.models.feature_preference import FeaturePreference
from app.repositories.feature_preference_repository import (
    FeaturePreferenceRepository,
)


class FeaturePreferenceValidationError(Exception):
    pass


class FeaturePreferenceService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = FeaturePreferenceRepository(db)

    @staticmethod
    def _validate_preferences(
        feature_preferences: dict[str, str],
    ) -> dict[str, str]:
        if not isinstance(feature_preferences, dict):
            raise FeaturePreferenceValidationError(
                "Feature preferences must be a dictionary."
            )

        normalized: dict[str, str] = {}

        for feature, preference in feature_preferences.items():
            if not isinstance(feature, str):
                raise FeaturePreferenceValidationError(
                    "Feature names must be strings."
                )

            feature = feature.strip()

            if not feature:
                raise FeaturePreferenceValidationError(
                    "Feature names cannot be empty."
                )

            if len(feature) > 100:
                raise FeaturePreferenceValidationError(
                    "Feature names cannot exceed 100 characters."
                )

            if not isinstance(preference, str):
                raise FeaturePreferenceValidationError(
                    "Preference values must be strings."
                )

            preference = preference.strip()

            if not preference:
                raise FeaturePreferenceValidationError(
                    "Preference values cannot be empty."
                )

            if len(preference) > 50:
                raise FeaturePreferenceValidationError(
                    "Preference values cannot exceed 50 characters."
                )

            normalized[feature] = preference

        return normalized

    def get_for_user(
        self,
        user_id: UUID,
    ) -> list[FeaturePreference]:
        return self.repository.get_by_user_id(user_id)

    def replace_for_user(
        self,
        user_id: UUID,
        feature_preferences: dict[str, str],
    ) -> list[FeaturePreference]:
        normalized = self._validate_preferences(feature_preferences)

        try:
            records = self.repository.replace_for_user(
                user_id=user_id,
                feature_preferences=normalized,
            )
            self.db.commit()

            for record in records:
                self.db.refresh(record)

            return records

        except Exception:
            self.db.rollback()
            raise