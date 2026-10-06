from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.notification_preference import NotificationPreference


class NotificationPreferenceRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_user_id(
        self,
        user_id: UUID,
    ) -> NotificationPreference | None:
        return self.db.scalar(
            select(NotificationPreference).where(
                NotificationPreference.user_id == user_id
            )
        )

    def upsert(
        self,
        user_id: UUID,
        enabled: bool,
        daily_drop_enabled: bool,
        group_activity_enabled: bool,
        quiet_hours_start: int | None = None,
        quiet_hours_end: int | None = None,
    ) -> NotificationPreference:
        notification_preference = self.get_by_user_id(user_id)

        if notification_preference is None:
            notification_preference = NotificationPreference(
                user_id=user_id,
                enabled=enabled,
                daily_drop_enabled=daily_drop_enabled,
                group_activity_enabled=group_activity_enabled,
                quiet_hours_start=quiet_hours_start,
                quiet_hours_end=quiet_hours_end,
            )

            self.db.add(notification_preference)
        else:
            notification_preference.enabled = enabled
            notification_preference.daily_drop_enabled = (
                daily_drop_enabled
            )
            notification_preference.group_activity_enabled = (
                group_activity_enabled
            )
            notification_preference.quiet_hours_start = (
                quiet_hours_start
            )
            notification_preference.quiet_hours_end = (
                quiet_hours_end
            )

        self.db.flush()

        return notification_preference