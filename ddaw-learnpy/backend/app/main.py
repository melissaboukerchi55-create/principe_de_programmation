"""LearnPy API — FastAPI application entrypoint."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import SessionLocal, init_db, wait_for_db
from app.core.seed import seed_if_empty
from app.routers import auth, categories, courses, enrollments, lessons, users

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("learnpy")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown hooks (modern FastAPI replacement for on_event)."""
    logger.info("Starting %s v%s", settings.app_name, settings.app_version)
    wait_for_db()
    init_db()
    with SessionLocal() as db:
        seed_if_empty(db)
    yield
    logger.info("Shutting down %s", settings.app_name)


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "LearnPy — Online learning platform (React / Node.js / Django).\n\n"
            "Demonstrates **One-to-One** (User↔Profile), **One-to-Many** "
            "(Category→Course, Course→Lesson) and **Many-to-Many** (Student↔Course "
            "via Enrollment with attributes)."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url=f"{settings.api_prefix}/openapi.json",
        lifespan=lifespan,
    )

    origins = ["*"] if settings.cors_origins == "*" else settings.cors_origins.split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    for router in (auth.router, users.router, categories.router, courses.router,
                   lessons.router, enrollments.router):
        app.include_router(router, prefix=settings.api_prefix)

    @app.get("/health", tags=["meta"], summary="Liveness probe")
    def health():
        return {"status": "ok", "app": settings.app_name, "version": settings.app_version}

    @app.get("/", tags=["meta"], summary="Root")
    def root():
        return {
            "app": settings.app_name,
            "version": settings.app_version,
            "docs": "/docs",
            "api": settings.api_prefix,
        }

    return app


app = create_app()
