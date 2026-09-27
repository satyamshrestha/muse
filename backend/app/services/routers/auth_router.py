from fastapi import APIRouter, Depends
from uuid import UUID

from app.services.user_service import UserService
from app.auth.jwt import create_access_token, get_current_user_id
from app.exceptions.user_exceptions import UserNotFoundException
from app.services.dependencies import get_user_service
from app.auth.jwt import (
    create_access_token,
    create_refresh_token,
    get_current_user_id,
    verify_refresh_token,
)
from app.schemas.user_schema import (
    UserCreate,
    UserResponse,
    UserLogin,
    TokenResponse,
    RefreshTokenRequest
)

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup", response_model=UserResponse, status_code=201)
def signup(
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
    refresh_token = create_refresh_token(str(user.id))

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }

@router.get("/me", response_model=UserResponse)
def get_me(
    user_id: UUID = Depends(get_current_user_id),
    service: UserService = Depends(get_user_service),
):
    user = service.get_by_id(user_id)

    if not user:
        raise UserNotFoundException()

    return user

@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    request: RefreshTokenRequest,
    service: UserService = Depends(get_user_service),
):
    user_id = verify_refresh_token(request.refresh_token)

    user = service.get_by_id(user_id)

    if not user:
        raise UserNotFoundException()

    access_token = create_access_token(str(user.id))

    return {
        "access_token": access_token,
        "refresh_token": request.refresh_token,
        "token_type": "bearer",
    }