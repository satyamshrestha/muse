from fastapi import APIRouter

from app.services.routers import (
    auth_router,
    device_router,
    group_router,
    notification_router,
    personalization_router,
    reminder_router,
)

api = APIRouter(prefix="/api/v1")

api.include_router(auth_router.router)
api.include_router(personalization_router.router)
api.include_router(group_router.router)
api.include_router(device_router.router)
api.include_router(notification_router.router)
api.include_router(reminder_router.router)