from fastapi import FastAPI

from app.api.v1.api import api as api_v1_api
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
)
app.include_router(api_v1_api)


@app.get("/health")
def health_check():
    return {"status": "ok"}