from fastapi import APIRouter

from app.services.routers import (
    auth_router,
)

api = APIRouter(prefix="/api/v1")

api.include_router(auth_router.router)