from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.db import init_db
from app.logger import get_logger, setup_logging
from app.routes import api_router
from app.version import APP_VERSION

STATIC_DIR = Path(__file__).resolve().parent / "app" / "static"
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    settings = get_settings()
    settings.validate_production()
    init_db()
    logger.info("Lite Analytics Core v%s started", APP_VERSION)
    yield


def create_app() -> FastAPI:
    settings = get_settings()

    application = FastAPI(
        title="Lite Analytics Core",
        description="Lightweight self-hosted analytics and web push subscription core",
        version=APP_VERSION,
        lifespan=lifespan,
    )

    @application.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        logger.warning("Validation error on %s: %s", request.url.path, exc.errors())
        return await request_validation_exception_handler(request, exc)

    origins = settings.allowed_origins_list
    if origins:
        application.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["*"],
        )

    application.include_router(api_router)
    application.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @application.get("/sw.js", include_in_schema=False)
    async def service_worker():
        return FileResponse(
            STATIC_DIR / "sw.js",
            media_type="application/javascript",
        )

    return application


app = create_app()
