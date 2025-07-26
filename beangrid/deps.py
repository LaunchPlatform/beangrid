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


def get_workdir() -> Path:
    workdir = os.getenv("WORKDIR")
    if not workdir:
        raise HTTPException(
            status_code=403, detail="WORKDIR environment variable not set"
        )
    workdir_path = Path(workdir)
    if not workdir_path.exists() or not workdir_path.is_dir():
        raise HTTPException(
            status_code=403, detail="WORKDIR does not exist or is not a directory"
        )
    return workdir_path


def get_yaml_file_path(workdir: Path = Depends(get_workdir)) -> Path:
    file_path = workdir / "workbook.yaml"
    if not file_path.exists():
        raise HTTPException(status_code=403, detail="Workbook file not found")
    return file_path


def get_yaml_content(file_path: Path = Depends(get_yaml_file_path)) -> str:
    return file_path.read_text(encoding="utf-8")


TemplatesDeps = Annotated[Jinja2Templates, Depends(get_templates)]
YAMLFilePathDeps = Annotated[Path, Depends(get_yaml_file_path)]
YAMLContentDeps = Annotated[str, Depends(get_yaml_content)]
WorkdirDeps = Annotated[Path, Depends(get_workdir)]
