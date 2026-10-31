from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.behavioral_signal import BehavioralSignal


class BehavioralSignalRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        user_id: UUID,
        signal_type: str,
        value: str,
    ) -> BehavioralSignal:
        signal = BehavioralSignal(
            user_id=user_id,
            signal_type=signal_type,
            value=value,
        )
        self.db.add(signal)
        self.db.flush()
        return signal

    def get_by_id(self, signal_id: UUID) -> BehavioralSignal | None:
        return self.db.scalar(
            select(BehavioralSignal).where(
                BehavioralSignal.id == signal_id
            )
        )

    def get_for_user(self, user_id: UUID) -> list[BehavioralSignal]:
        statement = (
            select(BehavioralSignal)
            .where(BehavioralSignal.user_id == user_id)
            .order_by(BehavioralSignal.created_at.asc())
        )
        return list(self.db.scalars(statement))

    def get_by_type(
        self,
        user_id: UUID,
        signal_type: str,
    ) -> list[BehavioralSignal]:
        statement = (
            select(BehavioralSignal)
            .where(
                BehavioralSignal.user_id == user_id,
                BehavioralSignal.signal_type == signal_type,
            )
            .order_by(BehavioralSignal.created_at.asc())
        )
        return list(self.db.scalars(statement))

    def delete(self, signal_id: UUID) -> bool:
        result = self.db.execute(
            delete(BehavioralSignal).where(
                BehavioralSignal.id == signal_id
            )
        )
        self.db.flush()
        return result.rowcount > 0