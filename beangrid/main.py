from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from .core.config import settings
from .views import api as api_router
from .views import home as home_router


def make_app() -> FastAPI:
    app = FastAPI(title="BeanGrid", version="1.0.0")

    # Add session middleware
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.SESSION_SECRET_KEY,
        max_age=settings.SESSION_MAX_AGE,
    )

    # Mount static files
    app.mount("/static", StaticFiles(directory="beangrid/static"), name="static")

    # Include routers
    app.include_router(home_router.router)
    app.include_router(api_router.router)

    return app
