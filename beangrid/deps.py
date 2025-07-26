import os
from pathlib import Path
from typing import Annotated

from fastapi import Depends
from fastapi import HTTPException
from fastapi import Request
from fastapi.templating import Jinja2Templates

# Get the templates directory
TEMPLATES_DIR = Path(__file__).parent / "templates"


def get_templates() -> Jinja2Templates:
    """Dependency to get Jinja2 templates."""
    return Jinja2Templates(directory=str(TEMPLATES_DIR))


TemplatesDeps = Annotated[Jinja2Templates, Depends(get_templates)]


def get_yaml_file_path() -> Path:
    workbook_file = os.getenv("WORKBOOK_FILE")
    if not workbook_file:
        # Use default sample workbook if not provided
        workbook_file = str(Path(__file__).parent.parent / "sample_workbook.yaml")
    file_path = Path(workbook_file)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Workbook file not found")
    return file_path


def get_yaml_content(file_path: Path = Depends(get_yaml_file_path)) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


YAMLFilePath = Annotated[Path, Depends(get_yaml_file_path)]
YAMLContent = Annotated[str, Depends(get_yaml_content)]
