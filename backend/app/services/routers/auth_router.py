from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.user_repository import UserRepository
from app.services.user_service import UserService
from app.auth.jwt import create_access_token, get_current_user_id
from app.exceptions.user_exceptions import UserNotFoundException
from app.schemas.user_schema import (
    UserCreate,
    UserResponse,
    UserLogin,
    TokenResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    repository = UserRepository(db)
    return UserService(repository)


@router.post("/signup", response_model=UserResponse, status_code=201)
def create_user(
    user: UserCreate,
    service: UserService = Depends(get_user_service),
):
    return service.create_user(
        email=user.email,
        password=user.password,
        display_name=user.display_name,
    )


@router.post("/login", response_model=TokenResponse)
def login(
    credentials: UserLogin,
    service: UserService = Depends(get_user_service),
):
    user = service.login(
        email=credentials.email,
        password=credentials.password,
    )

    access_token = create_access_token(str(user.id))

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }

@router.get("/me", response_model=UserResponse)
def get_me(
    user_id: str = Depends(get_current_user_id),
    service: UserService = Depends(get_user_service),
):
    user = service.get_by_id(user_id)

    if not user:
        raise UserNotFoundException()

    return user