from pathlib import Path
from typing import Annotated

from fastapi import Depends
from fastapi import Request
from fastapi.templating import Jinja2Templates

# Get the templates directory
TEMPLATES_DIR = Path(__file__).parent / "templates"


def get_templates() -> Jinja2Templates:
    """Dependency to get Jinja2 templates."""
    return Jinja2Templates(directory=str(TEMPLATES_DIR))


TemplatesDeps = Annotated[Jinja2Templates, Depends(get_templates)]
