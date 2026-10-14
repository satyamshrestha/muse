from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.models.notification import Notification


class NotificationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        user_id: UUID,
        notification_type: str,
        title: str,
        body: str | None = None,
        reference_type: str | None = None,
        reference_id: UUID | None = None,
    ) -> Notification:
        notification = Notification(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            body=body,
            reference_type=reference_type,
            reference_id=reference_id,
        )
        self.db.add(notification)
        self.db.flush()
        return notification

    def get_by_id_for_user(
        self,
        notification_id: UUID,
        user_id: UUID,
    ) -> Notification | None:
        statement = select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )
        return self.db.scalar(statement)

    def list_by_user(
        self,
        user_id: UUID,
        limit: int = 20,
        offset: int = 0,
        unread_only: bool = False,
    ) -> list[Notification]:
        statement = select(Notification).where(
            Notification.user_id == user_id
        )

        if unread_only:
            statement = statement.where(Notification.read_at.is_(None))

        statement = (
            statement
            .order_by(
                Notification.created_at.desc(),
                Notification.id.desc(),
            )
            .offset(offset)
            .limit(limit)
        )

        return list(self.db.scalars(statement).all())

    def count_unread(self, user_id: UUID) -> int:
        statement = select(func.count()).select_from(Notification).where(
            Notification.user_id == user_id,
            Notification.read_at.is_(None),
        )
        return self.db.scalar(statement) or 0

    def mark_read(
        self,
        notification: Notification,
    ) -> Notification:
        if notification.read_at is None:
            notification.read_at = datetime.now(timezone.utc)
            self.db.flush()

        return notification

    def mark_all_read(self, user_id: UUID) -> int:
        statement = (
            update(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.read_at.is_(None),
            )
            .values(read_at=datetime.now(timezone.utc))
            .execution_options(synchronize_session="fetch")
        )
        result = self.db.execute(statement)
        return result.rowcount or 0