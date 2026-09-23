from app.auth.hashing import hash_password
from app.models.user import User
from app.repositories.user_repository import UserRepository


class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    def get_by_email(self, email: str) -> User | None:
        return self.repository.get_by_email(email)

    def create_user(
        self,
        email: str,
        password: str,
        display_name: str,
    ) -> User:
        existing_user = self.repository.get_by_email(email)

        if existing_user:
            raise ValueError("User with this email already exists")

        return self.repository.create(
            email=email,
            password_hash=hash_password(password),
            display_name=display_name,
        )