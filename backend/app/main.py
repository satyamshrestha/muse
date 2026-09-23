from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.v1.api import api as api_v1_api
from app.core.config import settings
from app.exceptions.app_exception import AppException

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
)
app.include_router(api_v1_api)

@app.exception_handler(AppException)
async def app_exception_handler(
    request: Request,
    exc: AppException
):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail
        }
    )


@app.get("/health")
def health_check():
    return {"status": "ok"}