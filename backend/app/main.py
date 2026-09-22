from fastapi import FastAPI

from app.api.v1.router import router as api_v1_router
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
)
app.include_router(api_v1_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}