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

    def update_display_name(
        self,
        user_id: UUID,
        display_name: str
    ):
        user = self,get_by_id(user_id)
        if not user:
            return None
        user.display_name = display_name
        self.db.commit()
        self.db.refresh(user)
        
        return user