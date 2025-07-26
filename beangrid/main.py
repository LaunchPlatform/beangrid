from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .views.api import router as api_router
from .views.home import router as home_router


def make_app() -> FastAPI:
    app = FastAPI()

    # Mount static files
    static_path = Path(__file__).parent / "static"
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

    app.include_router(home_router)
    app.include_router(api_router)
    return app
