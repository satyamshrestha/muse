from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.user_preference import UserPreference


class UserPreferenceRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_user_id(
        self,
        user_id: UUID,
    ) -> list[UserPreference]:
        return list(
            self.db.scalars(
                select(UserPreference).where(
                    UserPreference.user_id == user_id
                )
            )
        )

    def replace_for_user(
        self,
        user_id: UUID,
        preferences: dict[str, str],
    ) -> list[UserPreference]:
        self.db.execute(
            delete(UserPreference).where(
                UserPreference.user_id == user_id
            )
        )

        records = [
            UserPreference(
                user_id=user_id,
                key=key,
                value=value,
            )
            for key, value in preferences.items()
        ]

        self.db.add_all(records)
        self.db.flush()

        return records