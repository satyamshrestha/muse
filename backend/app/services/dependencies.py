from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
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
from app.services.personalization_service import PersonalizationService
from app.services.user_service import UserService
from app.repositories.friend_group_repository import FriendGroupRepository
from app.repositories.group_membership_repository import GroupMembershipRepository
from app.services.group_service import GroupService


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
    invitation_service = InvitationCodeService(invitation_repository)

    configuration_repository = BaseConfigurationRepository(db)

    user_interest_repository = UserInterestRepository(db)
    user_preference_repository = UserPreferenceRepository(db)
    feature_preference_repository = FeaturePreferenceRepository(db)
    notification_preference_repository = (
        NotificationPreferenceRepository(db)
    )

    return PersonalizationService(
        user_repository=user_repository,
        invitation_service=invitation_service,
        configuration_repository=configuration_repository,
        user_interest_repository=user_interest_repository,
        user_preference_repository=user_preference_repository,
        feature_preference_repository=feature_preference_repository,
        notification_preference_repository=notification_preference_repository,
    )

def get_group_service(
    db: Session = Depends(get_db),
) -> GroupService:
    group_repository = FriendGroupRepository(db)
    membership_repository = GroupMembershipRepository(db)

    return GroupService(
        group_repository=group_repository,
        membership_repository=membership_repository,
    )