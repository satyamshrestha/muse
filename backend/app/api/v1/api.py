from fastapi import APIRouter

from app.services.routers import (
    user_router
)

api = APIRouter(prefix="/api/v1")

api.include_router(user_router.router)