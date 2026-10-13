from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.device import Device


class DeviceRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        user_id: UUID,
        device_token: str,
        platform: str,
    ) -> Device:
        device = Device(
            user_id=user_id,
            device_token=device_token,
            platform=platform,
        )

        self.db.add(device)
        self.db.flush()

        return device

    def get_by_token(self, device_token: str) -> Device | None:
        return self.db.scalar(
            select(Device).where(
                Device.device_token == device_token
            )
        )

    def get_by_id_for_user(
        self,
        device_id: UUID,
        user_id: UUID,
    ) -> Device | None:
        return self.db.scalar(
            select(Device).where(
                Device.id == device_id,
                Device.user_id == user_id,
            )
        )

    def list_by_user(self, user_id: UUID) -> list[Device]:
        statement = (
            select(Device)
            .where(Device.user_id == user_id)
            .order_by(Device.created_at.desc(), Device.id)
        )

        return list(self.db.scalars(statement).all())

    def update_platform(
        self,
        device: Device,
        platform: str,
    ) -> Device:
        device.platform = platform
        self.db.flush()

        return device

    def delete(self, device: Device) -> None:
        self.db.delete(device)
        self.db.flush()