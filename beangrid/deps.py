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

# Get the templates directory
TEMPLATES_DIR = Path(__file__).parent / "templates"


def get_templates() -> Jinja2Templates:
    """Dependency to get Jinja2 templates."""
    return Jinja2Templates(directory=str(TEMPLATES_DIR))


def get_workdir(request: Request) -> Path:
    # Check for existing session UUID in cookies
    session_uuid = request.cookies.get("workdir_uuid")

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

    # Initialize sample workbook.yaml
    sample_workbook = """sheets:
  - name: Sales
    cells:
      - id: A1
        value: Product
      - id: B1
        value: Price
      - id: C1
        value: Quantity
      - id: D1
        value: Total
      - id: A2
        value: Widget A
      - id: B2
        value: "10.50"
      - id: C2
        value: "4"
      - id: D2
        formula: "=B2*C2"
      - id: A3
        value: Widget B
      - id: B3
        value: "15.75"
      - id: C3
        value: "5"
      - id: D3
        formula: "=B3*C3"
      - id: A4
        value: Widget C
      - id: B4
        value: "8.25"
      - id: C4
        value: "7"
      - id: D4
        formula: "=B4*C4"
      - id: A5
        value: Total
      - id: B5
        value: ""
      - id: C5
        value: ""
      - id: D5
        formula: "=SUM(D2:D4)"
  - name: Summary
    cells:
      - id: A1
        value: Summary
      - id: B1
        value: Value
      - id: A2
        value: Total Sales
      - id: B2
        formula: "=Sales!D5"
      - id: A3
        value: Average Price
      - id: B3
        formula: "=AVERAGE(Sales!B2:B4)"
      - id: A4
        value: Max Price
      - id: B4
        formula: "=MAX(Sales!B2:B4)"
      - id: A5
        value: Min Price
      - id: B5
        formula: "=MIN(Sales!B2:B4)"
"""

    workbook_file = workdir_path / "workbook.yaml"
    workbook_file.write_text(sample_workbook, encoding="utf-8")

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

    # Set cookie for session management
    request.cookies["workdir_uuid"] = new_uuid

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
