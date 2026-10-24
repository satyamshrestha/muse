from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.base_configuration_repository import BaseConfigurationRepository
from app.repositories.feature_preference_repository import FeaturePreferenceRepository
from app.repositories.invitation_code_repository import InvitationCodeRepository
from app.repositories.notification_preference_repository import NotificationPreferenceRepository
from app.repositories.user_interest_repository import UserInterestRepository
from app.repositories.user_preference_repository import UserPreferenceRepository
from app.repositories.friend_group_repository import FriendGroupRepository
from app.repositories.group_membership_repository import GroupMembershipRepository
from app.repositories.reminder_repository import ReminderRepository
from app.repositories.group_invitation_repository import GroupInvitationRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.user_repository import UserRepository
from app.services.invitation_code_service import InvitationCodeService
from app.services.personalization_service import PersonalizationService
from app.services.user_service import UserService
from app.services.group_service import GroupService
from app.repositories.device_repository import DeviceRepository
from app.services.device_service import DeviceService
from app.services.notification_service import NotificationService
from app.services.notification_preference_service import NotificationPreferenceService
from app.services.reminder_service import ReminderService
from app.services.user_interest_service import UserInterestService
from app.services.mood_entry_service import MoodEntryService
from app.services.personal_note_service import PersonalNoteService
from app.services.feature_preference_service import FeaturePreferenceService
from app.services.group_activity_service import GroupActivityService
from app.services.group_activity_response_service import GroupActivityResponseService
from app.services.shared_note_service import SharedNoteService


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
    invitation_repository=GroupInvitationRepository(db)

    return GroupService(
        group_repository=group_repository,
        membership_repository=membership_repository,
        invitation_repository=invitation_repository,
    )

def get_device_service(db: Session = Depends(get_db)) -> DeviceService:
    return DeviceService(DeviceRepository(db))

def get_notification_service(db: Session = Depends(get_db)) -> NotificationService:
    return NotificationService(
        repository=NotificationRepository(db),
        preference_repository=NotificationPreferenceRepository(db),
    )

def get_reminder_service(db=Depends(get_db)) -> ReminderService:
    return ReminderService(db)

def get_user_interest_service(db=Depends(get_db)) -> UserInterestService:
    return UserInterestService(db)

def get_mood_entry_service(db=Depends(get_db)) -> MoodEntryService:
    return MoodEntryService(db)

def get_personal_note_service(db=Depends(get_db)) -> PersonalNoteService:
    return PersonalNoteService(db)

def get_feature_preference_service(db: Session = Depends(get_db),) -> FeaturePreferenceService:
    return FeaturePreferenceService(db)

def get_notification_preference_service(db: Session = Depends(get_db)) -> NotificationPreferenceService:
    return NotificationPreferenceService(db)

def get_group_activity_service(db: Session = Depends(get_db)) -> GroupActivityService:
    return GroupActivityService(db)

def get_group_activity_response_service(db: Session = Depends(get_db)) -> GroupActivityResponseService:
    return GroupActivityResponseService(db)

def get_shared_note_service(db: Session = Depends(get_db)) -> SharedNoteService:
    return SharedNoteService(db)