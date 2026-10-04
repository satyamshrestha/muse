from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_email(self, email: str) -> User | None:
        return self.db.scalar(
            select(User).where(User.email == email)
        )

    def create(
        self,
        email: str,
        password_hash: str,
        display_name: str,
    ) -> User:
        user = User(
            email=email,
            password_hash=password_hash,
            display_name=display_name,
        )

        self.db.add(user)
        self.db.flush()

        return user

    def get_by_id(
        self,
        user_id: UUID
    ) -> User | None:
        return self.db.scalar(
            select(User).where(User.id == user_id)
        )

    def update_profile(
        self,
        user_id: UUID,
        display_name: str | None = None,
        bio: str | None = None,
    ) -> User | None:
        user = self.get_by_id(user_id)

        if not user:
            return None

        if display_name is not None:
            user.display_name = display_name

        if bio is not None:
            user.bio = bio

        self.db.commit()
        self.db.refresh(user)

        return user

    def update_password(
        self,
        user_id: UUID,
        password_hash: str,
    ) -> User | None:
        user = self.get_by_id(user_id)

        if not user:
            return None

        user.password_hash = password_hash

        self.db.commit()
        self.db.refresh(user)

        return user

    def attach_base_configuration(
        self,
        user_id: UUID,
        configuration_id: UUID,
    ) -> User | None:
        user = self.get_by_id(user_id)

        if not user:
            return None

        user.base_configuration_id = configuration_id

        self.db.commit()
        self.db.refresh(user)

        return user