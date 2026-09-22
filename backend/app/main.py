from fastapi import FastAPI

from app.services.routers.user_router import router as user_router
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
)

app.include_router(user_router)