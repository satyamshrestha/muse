from fastapi import APIRouter

from app.services.routers.user_router import router as user_router

router = APIRouter(prefix="/api/v1")

router.include_router(user_router)