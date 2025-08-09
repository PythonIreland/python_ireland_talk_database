"""FastAPI application entrypoint.

- Configures CORS.
- Mounts API routers under /api/v1.
- Exposes a root ("/") endpoint with basic status.

This stays thin; business logic is in app/service, and data access in db/.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routers.health import router as health_router
from backend.api.routers import talks as talks_router_module
from backend.api.routers import taxonomies as taxonomies_router_module
from backend.api.routers import ingest as ingest_router_module
from backend.api.routers import analytics as analytics_router_module

# Added: logging and simple error handling middleware
import logging
import os
import time
import uuid
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi import HTTPException as FastAPIHTTPException
from starlette.exceptions import HTTPException as StarletteHTTPException


def _setup_logging() -> logging.Logger:
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logger = logging.getLogger("app")
    if not logger.handlers:
        # Only configure once to avoid duplicate handlers under reload
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            fmt="%(asctime)s %(levelname)s %(name)s: %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S%z",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(level)
    return logger


logger = _setup_logging()


def create_app() -> FastAPI:
    app = FastAPI(title="Python Ireland Talk Database", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def request_logger(request: Request, call_next):
        start = time.perf_counter()
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        try:
            response = await call_next(request)
        except (FastAPIHTTPException, StarletteHTTPException):
            # Let FastAPI/Starlette handle HTTP errors; we still log below via a separate middleware or rely on default logging.
            raise
        except Exception:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.exception(
                "Unhandled error: %s %s -> 500 in %sms req_id=%s",
                request.method,
                request.url.path,
                duration_ms,
                request_id,
            )
            content = {"detail": "Internal Server Error", "request_id": request_id}
            response = JSONResponse(status_code=500, content=content)
            response.headers["X-Request-ID"] = request_id
            return response

        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.info(
            "%s %s -> %s in %sms req_id=%s",
            request.method,
            request.url.path,
            getattr(response, "status_code", 0),
            duration_ms,
            request_id,
        )
        # Propagate request id
        try:
            response.headers["X-Request-ID"] = request_id
        except Exception:
            pass
        return response

    # Routers
    app.include_router(health_router, prefix="/api/v1")
    app.include_router(talks_router_module.router, prefix="/api/v1")
    app.include_router(taxonomies_router_module.router, prefix="/api/v1")
    app.include_router(ingest_router_module.router, prefix="/api/v1")
    app.include_router(analytics_router_module.router, prefix="/api/v1")

    @app.get("/")
    async def root():
        return {
            "message": "Python Ireland Talk Database API",
            "version": "0.1.0",
            "status": "ok",
        }

    return app


app = create_app()
