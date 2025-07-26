from fastapi import APIRouter
from fastapi import Request
from fastapi.responses import HTMLResponse

from ..deps import TemplatesDeps

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def home(request: Request, templates: TemplatesDeps):
    return templates.TemplateResponse("home.html", {"request": request})
