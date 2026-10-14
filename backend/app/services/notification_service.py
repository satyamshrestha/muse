from datetime import datetime, timezone
from uuid import UUID

from app.models.notification import Notification
from app.models.notification_preference import NotificationPreference
from app.repositories.notification_preference_repository import (
    NotificationPreferenceRepository,
)
from app.repositories.notification_repository import NotificationRepository


class NotificationNotFoundError(Exception):
    """Raised when a notification is unavailable to its owner."""


class NotificationPreferenceError(Exception):
    """Raised when notification preferences are invalid."""


class NotificationService:
    CATEGORY_PREFERENCE_FIELDS = {
        "daily_drop": "daily_drop_enabled",
        "group_activity": "group_activity_enabled",
    }

    def __init__(
        self,
        repository: NotificationRepository,
        preference_repository: NotificationPreferenceRepository,
    ):
        self.repository = repository
        self.preference_repository = preference_repository
        self.db = repository.db

    def create_for_user(
        self,
        user_id: UUID,
        notification_type: str,
        title: str,
        body: str | None = None,
        reference_type: str | None = None,
        reference_id: UUID | None = None,
    ) -> Notification | None:
        try:
            preference = self.preference_repository.get_by_user_id(user_id)

            if preference is not None and not self._is_enabled(
                preference,
                notification_type,
            ):
                return None

            notification = self.repository.create(
                user_id=user_id,
                notification_type=notification_type,
                title=title,
                body=body,
                reference_type=reference_type,
                reference_id=reference_id,
            )
            self.db.commit()
            self.db.refresh(notification)
            return notification
        except Exception:
            self.db.rollback()
            raise

    def list_for_user(
        self,
        user_id: UUID,
        limit: int = 20,
        offset: int = 0,
        unread_only: bool = False,
    ) -> list[Notification]:
        return self.repository.list_by_user(
            user_id=user_id,
            limit=limit,
            offset=offset,
            unread_only=unread_only,
        )

    def unread_count(self, user_id: UUID) -> int:
        return self.repository.count_unread(user_id)

    def mark_read(
        self,
        user_id: UUID,
        notification_id: UUID,
    ) -> Notification:
        try:
            notification = self.repository.get_by_id_for_user(
                notification_id=notification_id,
                user_id=user_id,
            )
            if notification is None:
                raise NotificationNotFoundError(
                    "Notification not found for this user."
                )

            self.repository.mark_read(notification)
            self.db.commit()
            self.db.refresh(notification)
            return notification
        except Exception:
            self.db.rollback()
            raise

    def mark_all_read(self, user_id: UUID) -> int:
        try:
            updated_count = self.repository.mark_all_read(user_id)
            self.db.commit()
            return updated_count
        except Exception:
            self.db.rollback()
            raise

    @classmethod
    def _is_enabled(
        cls,
        preference: NotificationPreference,
        notification_type: str,
    ) -> bool:
        if not preference.enabled:
            return False

        preference_field = cls.CATEGORY_PREFERENCE_FIELDS.get(
            notification_type
        )
        if preference_field is not None:
            return bool(getattr(preference, preference_field))

        return True

    @staticmethod
    def validate_quiet_hours(
        quiet_hours_start: int | None,
        quiet_hours_end: int | None,
    ) -> None:
        if (quiet_hours_start is None) != (quiet_hours_end is None):
            raise NotificationPreferenceError(
                "Quiet hours start and end must be provided together."
            )

        for hour in (quiet_hours_start, quiet_hours_end):
            if hour is not None and not 0 <= hour <= 23:
                raise NotificationPreferenceError(
                    "Quiet hours must be between 0 and 23."
                )

    @staticmethod
    def is_within_quiet_hours(
        preference: NotificationPreference,
        current_hour: int | None = None,
    ) -> bool:
        start = preference.quiet_hours_start
        end = preference.quiet_hours_end

        if start is None or end is None or start == end:
            return False

        hour = (
            datetime.now(timezone.utc).hour
            if current_hour is None
            else current_hour
        )
        if not 0 <= hour <= 23:
            raise NotificationPreferenceError(
                "Current hour must be between 0 and 23."
            )

        if start < end:
            return start <= hour < end

        return hour >= start or hour < end