from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.user_interest import UserInterest


class UserInterestRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_user_id(
        self,
        user_id: UUID,
    ) -> list[UserInterest]:
        return list(
            self.db.scalars(
                select(UserInterest).where(
                    UserInterest.user_id == user_id
                )
            )
        )

    def replace_for_user(
        self,
        user_id: UUID,
        interests: list[str],
    ) -> list[UserInterest]:
        self.db.execute(
            delete(UserInterest).where(
                UserInterest.user_id == user_id
            )
        )

        records = [
            UserInterest(
                user_id=user_id,
                interest=interest,
            )
            for interest in interests
        ]

        self.db.add_all(records)
        self.db.flush()

        return records