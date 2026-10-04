from uuid import UUID

from app.exceptions.user_exceptions import UserNotFoundException
from app.repositories.base_configuration_repository import (
    BaseConfigurationRepository,
)
from app.repositories.user_repository import UserRepository
from app.services.invitation_code_service import InvitationCodeService


class PersonalizationService:
    def __init__(
        self,
        user_repository: UserRepository,
        invitation_service: InvitationCodeService,
        configuration_repository: BaseConfigurationRepository,
    ):
        self.user_repository = user_repository
        self.invitation_service = invitation_service
        self.configuration_repository = configuration_repository

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
            raise ValueError(
                "Base configuration not found"
            )

        user.base_configuration_id = configuration.id

        self.user_repository.db.commit()
        self.user_repository.db.refresh(user)

        return configuration