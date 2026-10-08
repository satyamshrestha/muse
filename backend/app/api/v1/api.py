from fastapi import APIRouter

from app.services.routers import (
    auth_router,
    personalization_router,
    group_router,
)

api = APIRouter(prefix="/api/v1")

api.include_router(auth_router.router)
api.include_router(personalization_router.router)
api.include_router(group_router.router)