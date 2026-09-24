from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.user_repository import UserRepository
from app.schemas.user_schema import UserCreate, UserResponse, UserLogin
from app.services.user_service import UserService


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


@router.post("/login", response_model=UserResponse)
def login(
    credentials: UserLogin,
    service: UserService = Depends(get_user_service),
):
    return service.login(
        email=credentials.email,
        password=credentials.password,
    )