from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user_interest import UserInterest
from app.repositories.user_interest_repository import (
    UserInterestRepository,
)


class UserInterestValidationError(Exception):
    pass


class UserInterestService:
    MAX_INTERESTS = 50
    MAX_INTEREST_LENGTH = 100

    def __init__(self, db: Session):
        self.db = db
        self.repository = UserInterestRepository(db)

    @classmethod
    def _normalize_interests(
        cls,
        interests: list[str],
    ) -> list[str]:
        if len(interests) > cls.MAX_INTERESTS:
            raise UserInterestValidationError(
                f"You can have at most {cls.MAX_INTERESTS} interests."
            )

        normalized: list[str] = []
        seen: set[str] = set()

        for interest in interests:
            if not isinstance(interest, str):
                raise UserInterestValidationError(
                    "Each interest must be a string."
                )

            value = interest.strip()

            if not value:
                raise UserInterestValidationError(
                    "Interests cannot be empty."
                )

            if len(value) > cls.MAX_INTEREST_LENGTH:
                raise UserInterestValidationError(
                    "Each interest must be at most 100 characters."
                )

            # Deduplicate case-insensitively while preserving the
            # spelling and order of the first occurrence.
            key = value.casefold()
            if key not in seen:
                normalized.append(value)
                seen.add(key)

        return normalized

    def get_for_user(self, user_id: UUID) -> list[UserInterest]:
        return self.repository.get_by_user_id(user_id)

    def replace_for_user(
        self,
        user_id: UUID,
        interests: list[str],
    ) -> list[UserInterest]:
        normalized = self._normalize_interests(interests)

        try:
            records = self.repository.replace_for_user(
                user_id=user_id,
                interests=normalized,
            )
            self.db.commit()

            # Reload persisted records so callers receive database-backed
            # instances, including generated IDs and timestamps.
            return self.repository.get_by_user_id(user_id)
        except IntegrityError:
            self.db.rollback()
            raise UserInterestValidationError(
                "The interests could not be saved."
            ) from None
        except Exception:
            self.db.rollback()
            raise