from app.auth.hashing import hash_password, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.exceptions.user_exceptions import (
    UserAlreadyExistsException,
    InvalidCredentialsException
)


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
            raise UserAlreadyExistsException()

        user = self.repository.create(
            email=email,
            password_hash=hash_password(password),
            display_name=display_name,
        )

        self.repository.db.commit()

        return user

    def login(
        self,
        email: str,
        password: str
    ) -> User:
        user = self.repository.get_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise InvalidCredentialsException()        

        return user