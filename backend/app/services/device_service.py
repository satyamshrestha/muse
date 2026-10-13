from uuid import UUID

from sqlalchemy.exc import IntegrityError

from app.models.device import Device
from app.repositories.device_repository import DeviceRepository


class DeviceTokenConflictError(Exception):
    """Raised when a device token belongs to another user."""


class DeviceNotFoundError(Exception):
    """Raised when a device is not registered to the requested user."""


class DeviceService:
    def __init__(self, repository: DeviceRepository):
        self.repository = repository
        self.db = repository.db

    def register(
        self,
        user_id: UUID,
        device_token: str,
        platform: str,
    ) -> Device:
        try:
            existing = self.repository.get_by_token(device_token)

            if existing is not None:
                if existing.user_id != user_id:
                    raise DeviceTokenConflictError(
                        "This device token is already registered "
                        "to another user."
                    )

                if existing.platform != platform:
                    self.repository.update_platform(existing, platform)

                self.db.commit()
                self.db.refresh(existing)
                return existing

            device = self.repository.create(
                user_id=user_id,
                device_token=device_token,
                platform=platform,
            )

            self.db.commit()
            self.db.refresh(device)
            return device

        except IntegrityError:
            # Another transaction may have registered this unique token
            # after our initial lookup.
            self.db.rollback()

            try:
                existing = self.repository.get_by_token(device_token)

                if existing is None:
                    raise

                if existing.user_id != user_id:
                    raise DeviceTokenConflictError(
                        "This device token is already registered "
                        "to another user."
                    )

                if existing.platform != platform:
                    self.repository.update_platform(existing, platform)

                self.db.commit()
                self.db.refresh(existing)
                return existing

            except Exception:
                self.db.rollback()
                raise

        except Exception:
            self.db.rollback()
            raise

    def list_for_user(self, user_id: UUID) -> list[Device]:
        return self.repository.list_by_user(user_id)

    def update_platform(
        self,
        user_id: UUID,
        device_id: UUID,
        platform: str,
    ) -> Device:
        try:
            device = self.repository.get_by_id_for_user(
                device_id=device_id,
                user_id=user_id,
            )

            if device is None:
                raise DeviceNotFoundError(
                    "Device not found for this user."
                )

            self.repository.update_platform(device, platform)
            self.db.commit()
            self.db.refresh(device)
            return device

        except Exception:
            self.db.rollback()
            raise

    def unregister(
        self,
        user_id: UUID,
        device_id: UUID,
    ) -> None:
        try:
            device = self.repository.get_by_id_for_user(
                device_id=device_id,
                user_id=user_id,
            )

            if device is None:
                raise DeviceNotFoundError(
                    "Device not found for this user."
                )

            self.repository.delete(device)
            self.db.commit()

        except Exception:
            self.db.rollback()
            raise