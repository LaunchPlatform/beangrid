from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .views.home import router as home_router


def make_app() -> FastAPI:
    app = FastAPI()

    # Mount static files
    static_path = Path(__file__).parent / "static"
    if static_path.exists():
        app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

    app.include_router(home_router)
    return app
