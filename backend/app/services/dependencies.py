from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.base_configuration_repository import (
    BaseConfigurationRepository,
)
from app.repositories.invitation_code_repository import (
    InvitationCodeRepository,
)
from app.repositories.user_repository import UserRepository
from app.services.invitation_code_service import InvitationCodeService
from app.services.personalization_service import PersonalizationService
from app.services.user_service import UserService


def get_user_service(
    db: Session = Depends(get_db),
) -> UserService:
    repository = UserRepository(db)

    return UserService(repository)


def get_personalization_service(
    db: Session = Depends(get_db),
) -> PersonalizationService:
    user_repository = UserRepository(db)

    invitation_repository = InvitationCodeRepository(db)

    invitation_service = InvitationCodeService(
        invitation_repository
    )

    configuration_repository = BaseConfigurationRepository(db)

    return PersonalizationService(
        user_repository=user_repository,
        invitation_service=invitation_service,
        configuration_repository=configuration_repository,
    )