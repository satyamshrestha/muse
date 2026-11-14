from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy.orm import Session

from app.models.notification_preference import NotificationPreference
from app.repositories.notification_preference_repository import (
    NotificationPreferenceRepository,
)
from app.services.notification_service import (
    NotificationPreferenceError,
    NotificationService,
)


class NotificationPreferenceService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = NotificationPreferenceRepository(db)

    def get_for_user(
        self,
        user_id: UUID,
    ) -> NotificationPreference | None:
        return self.repository.get_by_user_id(user_id)

    def update_for_user(
        self,
        user_id: UUID,
        enabled: bool,
        daily_drop_enabled: bool,
        group_activity_enabled: bool,
        quiet_hours_start: int | None = None,
        quiet_hours_end: int | None = None,
        timezone_name: str = "UTC",
    ) -> NotificationPreference:
        NotificationService.validate_quiet_hours(
            quiet_hours_start,
            quiet_hours_end,
        )
        self.validate_timezone(timezone_name)

        try:
            preference = self.repository.upsert(
                user_id=user_id,
                enabled=enabled,
                daily_drop_enabled=daily_drop_enabled,
                group_activity_enabled=group_activity_enabled,
                quiet_hours_start=quiet_hours_start,
                quiet_hours_end=quiet_hours_end,
                timezone_name=timezone_name,
            )
            self.db.commit()
            self.db.refresh(preference)
            return preference
        except Exception:
            self.db.rollback()
            raise

    @staticmethod
    def validate_timezone(timezone_name: str) -> None:
        try:
            ZoneInfo(timezone_name)
        except (ZoneInfoNotFoundError, ValueError):
            raise NotificationPreferenceError(
                "Invalid timezone. Use a valid IANA timezone name."
            ) from None