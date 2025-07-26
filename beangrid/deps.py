import os
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Annotated

from fastapi import Depends
from fastapi import HTTPException
from fastapi import Request
from fastapi.templating import Jinja2Templates

from .scheme.cell import Cell
from .scheme.cell import Sheet
from .scheme.cell import Workbook


# Get the templates directory
TEMPLATES_DIR = Path(__file__).parent / "templates"


def create_sample_workbook() -> Workbook:
    """Create a sample workbook using Pydantic models."""
    sales_sheet = Sheet(
        name="Sales",
        cells=[
            Cell(id="A1", value="Product"),
            Cell(id="B1", value="Price"),
            Cell(id="C1", value="Quantity"),
            Cell(id="D1", value="Total"),
            Cell(id="A2", value="Widget A"),
            Cell(id="B2", value="10.50"),
            Cell(id="C2", value="4"),
            Cell(id="D2", formula="=B2*C2"),
            Cell(id="A3", value="Widget B"),
            Cell(id="B3", value="15.75"),
            Cell(id="C3", value="5"),
            Cell(id="D3", formula="=B3*C3"),
            Cell(id="A4", value="Widget C"),
            Cell(id="B4", value="8.25"),
            Cell(id="C4", value="7"),
            Cell(id="D4", formula="=B4*C4"),
            Cell(id="A5", value="Total"),
            Cell(id="B5", value=""),
            Cell(id="C5", value=""),
            Cell(id="D5", formula="=SUM(D2:D4)"),
        ],
    )

    summary_sheet = Sheet(
        name="Summary",
        cells=[
            Cell(id="A1", value="Summary"),
            Cell(id="B1", value="Value"),
            Cell(id="A2", value="Total Sales"),
            Cell(id="B2", formula="=Sales!D5"),
            Cell(id="A3", value="Average Price"),
            Cell(id="B3", formula="=AVERAGE(Sales!B2:B4)"),
            Cell(id="A4", value="Max Price"),
            Cell(id="B4", formula="=MAX(Sales!B2:B4)"),
            Cell(id="A5", value="Min Price"),
            Cell(id="B5", formula="=MIN(Sales!B2:B4)"),
        ],
    )

    return Workbook(sheets=[sales_sheet, summary_sheet])


def get_templates() -> Jinja2Templates:
    """Dependency to get Jinja2 templates."""
    return Jinja2Templates(directory=str(TEMPLATES_DIR))


def get_workdir(request: Request) -> Path:
    # Check for existing session UUID using Starlette sessions
    session_uuid = request.session.get("workdir_uuid")

    if session_uuid:
        # Validate UUID format
        try:
            uuid.UUID(session_uuid)
            # Try to use existing workdir
            workdir_path = Path(tempfile.gettempdir()) / f"beangrid_{session_uuid}"
            if workdir_path.exists() and workdir_path.is_dir():
                return workdir_path
        except ValueError:
            # Invalid UUID format, treat as no session
            pass

    # Create new workdir with UUID
    new_uuid = str(uuid.uuid4())
    workdir_path = Path(tempfile.gettempdir()) / f"beangrid_{new_uuid}"
    workdir_path.mkdir(parents=True, exist_ok=True)

    # Initialize sample workbook.yaml using Pydantic models
    workbook_file = workdir_path / "workbook.yaml"
    sample_workbook = create_sample_workbook()

    # Import here to avoid circular imports
    from .core.yaml_processor import save_workbook_to_yaml

    save_workbook_to_yaml(sample_workbook, workbook_file)

    # Initialize git repo
    try:
        subprocess.run(["git", "init"], cwd=workdir_path, check=True)
        subprocess.run(["git", "add", "workbook.yaml"], cwd=workdir_path, check=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"], cwd=workdir_path, check=True
        )
    except subprocess.CalledProcessError as e:
        # Git might not be available, continue without git
        pass

    # Set session for session management using Starlette
    request.session["workdir_uuid"] = new_uuid

    return workdir_path


def get_yaml_file_path(workdir: Path = Depends(get_workdir)) -> Path:
    file_path = workdir / "workbook.yaml"
    if not file_path.exists():
        raise HTTPException(status_code=403, detail="Workbook file not found")
    return file_path


def get_yaml_content(file_path: Path = Depends(get_yaml_file_path)) -> str:
    return file_path.read_text(encoding="utf-8")


def get_chat_file(workdir: Path = Depends(get_workdir)) -> Path:
    return workdir / "chat.jsonl"


TemplatesDeps = Annotated[Jinja2Templates, Depends(get_templates)]
YAMLFilePathDeps = Annotated[Path, Depends(get_yaml_file_path)]
YAMLContentDeps = Annotated[str, Depends(get_yaml_content)]
WorkdirDeps = Annotated[Path, Depends(get_workdir)]
ChatFileDeps = Annotated[Path, Depends(get_chat_file)]
