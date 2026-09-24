import logging

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.health import router as health_router
from app.api.v1.router import api_v1_router
from app.core.config import get_settings, validate_production_settings
from app.core.exceptions import AppError
from app.core.logging_config import configure_logging

logger = logging.getLogger(__name__)


def _error_envelope(code: str, message: str, details: object = None) -> dict:
    error: dict = {"code": code, "message": message}
    if details is not None:
        error["details"] = details
    return {"success": False, "error": error}


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()
    validate_production_settings(settings)

    app = FastAPI(title=settings.app_name)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content=_error_envelope(exc.code, exc.message))

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=_error_envelope(
                "VALIDATION_ERROR", "Invalid request data.", details=jsonable_encoder(exc.errors())
            ),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception while processing %s %s", request.method, request.url)
        return JSONResponse(
            status_code=500,
            content=_error_envelope("INTERNAL_SERVER_ERROR", "An unexpected error occurred."),
        )

    app.include_router(health_router)
    app.include_router(api_v1_router, prefix="/api/v1")

    return app


app = create_app()
