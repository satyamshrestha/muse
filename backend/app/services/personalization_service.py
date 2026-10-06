from uuid import UUID

from app.exceptions.user_exceptions import UserNotFoundException
from app.repositories.base_configuration_repository import (
    BaseConfigurationRepository,
)
from app.repositories.feature_preference_repository import (
    FeaturePreferenceRepository,
)
from app.repositories.invitation_code_repository import (
    InvitationCodeRepository,
)
from app.repositories.notification_preference_repository import (
    NotificationPreferenceRepository,
)
from app.repositories.user_interest_repository import (
    UserInterestRepository,
)
from app.repositories.user_preference_repository import (
    UserPreferenceRepository,
)
from app.repositories.user_repository import UserRepository
from app.services.invitation_code_service import InvitationCodeService


class PersonalizationService:
    def __init__(
        self,
        user_repository: UserRepository,
        invitation_service: InvitationCodeService,
        configuration_repository: BaseConfigurationRepository,
        user_interest_repository: UserInterestRepository,
        user_preference_repository: UserPreferenceRepository,
        feature_preference_repository: FeaturePreferenceRepository,
        notification_preference_repository: NotificationPreferenceRepository,
    ):
        self.user_repository = user_repository
        self.invitation_service = invitation_service
        self.configuration_repository = configuration_repository
        self.user_interest_repository = user_interest_repository
        self.user_preference_repository = user_preference_repository
        self.feature_preference_repository = feature_preference_repository
        self.notification_preference_repository = (
            notification_preference_repository
        )

    def claim_configuration(
        self,
        user_id: UUID,
        code: str,
    ):
        user = self.user_repository.get_by_id(user_id)

        if not user:
            raise UserNotFoundException()

        configuration_key = self.invitation_service.claim(code)

        configuration = self.configuration_repository.get_by_name(
            configuration_key
        )

        if not configuration:
            raise ValueError("Base configuration not found")

        user.base_configuration_id = configuration.id

        self.user_repository.db.commit()
        self.user_repository.db.refresh(user)

        return configuration

    def save_personalization(
        self,
        user_id: UUID,
        interests: list[str],
        preferences: dict[str, str],
        feature_preferences: dict[str, str],
        notification_enabled: bool,
        daily_drop_enabled: bool,
        group_activity_enabled: bool,
        quiet_hours_start: int | None = None,
        quiet_hours_end: int | None = None,
    ) -> None:
        user = self.user_repository.get_by_id(user_id)

        if not user:
            raise UserNotFoundException()

        self.user_interest_repository.replace_for_user(
            user_id=user_id,
            interests=interests,
        )

        self.user_preference_repository.replace_for_user(
            user_id=user_id,
            preferences=preferences,
        )

        self.feature_preference_repository.replace_for_user(
            user_id=user_id,
            feature_preferences=feature_preferences,
        )

        self.notification_preference_repository.upsert(
            user_id=user_id,
            enabled=notification_enabled,
            daily_drop_enabled=daily_drop_enabled,
            group_activity_enabled=group_activity_enabled,
            quiet_hours_start=quiet_hours_start,
            quiet_hours_end=quiet_hours_end,
        )

        self.user_repository.db.commit()