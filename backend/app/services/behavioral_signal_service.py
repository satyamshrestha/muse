from uuid import UUID

from sqlalchemy.orm import Session

from app.models.behavioral_signal import BehavioralSignal
from app.repositories.behavioral_signal_repository import (
    BehavioralSignalRepository,
)


class BehavioralSignalService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = BehavioralSignalRepository(db)

    def _get_signal(self, signal_id: UUID) -> BehavioralSignal:
        signal = self.repository.get_by_id(signal_id)

        if signal is None:
            raise ValueError("Behavioral signal not found")

        return signal

    def create_signal(
        self,
        user_id: UUID,
        signal_type: str,
        value: str,
    ) -> BehavioralSignal:
        if not signal_type.strip():
            raise ValueError("Signal type must not be empty")

        if not value.strip():
            raise ValueError("Signal value must not be empty")

        signal = self.repository.create(
            user_id=user_id,
            signal_type=signal_type,
            value=value,
        )
        self.db.commit()
        self.db.refresh(signal)
        return signal

    def get_user_signals(
        self,
        user_id: UUID,
    ) -> list[BehavioralSignal]:
        return self.repository.get_for_user(user_id)

    def get_user_signals_by_type(
        self,
        user_id: UUID,
        signal_type: str,
    ) -> list[BehavioralSignal]:
        if not signal_type.strip():
            raise ValueError("Signal type must not be empty")

        return self.repository.get_by_type(user_id, signal_type)

    def delete_signal(
        self,
        signal_id: UUID,
        user_id: UUID,
    ) -> bool:
        signal = self._get_signal(signal_id)

        if signal.user_id != user_id:
            raise ValueError("Cannot delete another user's signal")

        deleted = self.repository.delete(signal_id)

        if deleted:
            self.db.commit()

        return deleted