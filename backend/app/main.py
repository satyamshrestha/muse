from fastapi import FastAPI

from app.core.config import settings
from app.services.routers.user_router import router as user_router

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
)

app.include_router(user_router)

@app.get("/health")
def health_check():
    return {"status": "ok"}