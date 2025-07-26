import os
import subprocess
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List

import yaml
from fastapi import APIRouter
from fastapi import Body
from fastapi import HTTPException
from fastapi import Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from ..core.processor import FormulaProcessor
from ..core.yaml_processor import load_workbook_from_yaml
from ..core.yaml_processor import save_workbook_to_yaml
from ..scheme.cell import Cell
from ..scheme.cell import Workbook

SPREADSHEET_SCHEMA = Workbook.model_json_schema()

router = APIRouter(prefix="/api/v1")


class WorkbookResponse(BaseModel):
    """Response model for workbook data."""

    sheets: List[Dict[str, Any]]
    processed: bool
    error: str = None


class CellUpdateRequest(BaseModel):
    """Request model for updating a cell."""

    sheet_name: str
    cell_id: str
    value: str | None = None
    formula: str | None = None


class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []  # [{role: "user"|"assistant", content: str}]
    action: str | None = None  # e.g., "update_cell"
    action_args: dict | None = None


class ChatResponse(BaseModel):
    response: str
    action: str | None = None
    action_args: dict | None = None


@router.get("/workbook", response_model=WorkbookResponse)
async def get_workbook():
    """Get workbook data from the file specified by WORKBOOK_FILE environment variable."""
    workbook_file = os.getenv("WORKBOOK_FILE")

    if not workbook_file:
        # Use default sample workbook if not provided
        workbook_file = str(
            Path(__file__).parent.parent.parent / "sample_workbook.yaml"
        )

    file_path = Path(workbook_file)
    if not file_path.exists():
        raise HTTPException(
            status_code=404, detail=f"Workbook file not found: {workbook_file}"
        )

    try:
        # Load the workbook
        workbook = load_workbook_from_yaml(file_path)

        # Process the workbook with formulas
        processor = FormulaProcessor()
        processed_workbook = processor.process_workbook(workbook)

        # Convert to response format
        sheets_data = []
        for sheet in processed_workbook.sheets:
            sheet_data = {
                "name": sheet.name,
                "cells": [
                    {"id": cell.id, "value": cell.value, "formula": cell.formula}
                    for cell in sheet.cells
                ],
            }
            sheets_data.append(sheet_data)

        return WorkbookResponse(sheets=sheets_data, processed=True)

    except Exception as e:
        return WorkbookResponse(sheets=[], processed=False, error=str(e))


@router.get("/workbook/raw")
async def get_raw_workbook():
    """Get raw workbook data without processing formulas."""
    workbook_file = os.getenv("WORKBOOK_FILE")

    if not workbook_file:
        # Use default sample workbook if not provided
        workbook_file = str(
            Path(__file__).parent.parent.parent / "sample_workbook.yaml"
        )

    file_path = Path(workbook_file)
    if not file_path.exists():
        raise HTTPException(
            status_code=404, detail=f"Workbook file not found: {workbook_file}"
        )

    try:
        # Load the workbook without processing
        workbook = load_workbook_from_yaml(file_path)

        # Convert to response format
        sheets_data = []
        for sheet in workbook.sheets:
            sheet_data = {
                "name": sheet.name,
                "cells": [
                    {"id": cell.id, "value": cell.value, "formula": cell.formula}
                    for cell in sheet.cells
                ],
            }
            sheets_data.append(sheet_data)

        return {"sheets": sheets_data, "processed": False}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _get_workbook_file_path():
    """Get the workbook file path from environment or default."""
    workbook_file = os.getenv("WORKBOOK_FILE")

    if not workbook_file:
        workbook_file = str(
            Path(__file__).parent.parent.parent / "sample_workbook.yaml"
        )

    return Path(workbook_file)


@router.put("/workbook/cell")
async def update_cell(request: CellUpdateRequest = Body(...)):
    """Update a cell in the workbook and save to YAML file."""
    print(f"Received cell update request: {request}")
    try:
        file_path = _get_workbook_file_path()

        if not file_path.exists():
            raise HTTPException(
                status_code=404, detail=f"Workbook file not found: {file_path}"
            )

        # Load the current workbook
        workbook = load_workbook_from_yaml(file_path)

        # Find the sheet
        sheet = None
        for s in workbook.sheets:
            if s.name == request.sheet_name:
                sheet = s
                break

        if not sheet:
            raise HTTPException(
                status_code=404, detail=f"Sheet '{request.sheet_name}' not found"
            )

        # Find and update the cell
        cell_updated = False
        for cell in sheet.cells:
            if cell.id == request.cell_id:
                # Update cell values
                if request.value is not None:
                    cell.value = request.value if request.value.strip() else None
                    print(f"Updated cell {request.cell_id} value to: {cell.value}")
                if request.formula is not None:
                    cell.formula = request.formula if request.formula.strip() else None
                    print(f"Updated cell {request.cell_id} formula to: {cell.formula}")
                cell_updated = True
                break

        if not cell_updated:
            # Create new cell if it doesn't exist
            value = request.value if request.value and request.value.strip() else None
            formula = (
                request.formula if request.formula and request.formula.strip() else None
            )
            new_cell = Cell(id=request.cell_id, value=value, formula=formula)
            sheet.cells.append(new_cell)

        # Save the updated workbook back to YAML
        save_workbook_to_yaml(workbook, file_path)

        return {"message": "Cell updated successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workbook/cell/{sheet_name}/{cell_id}")
async def get_cell(sheet_name: str, cell_id: str):
    """Get a specific cell from the workbook."""
    try:
        file_path = _get_workbook_file_path()

        if not file_path.exists():
            raise HTTPException(
                status_code=404, detail=f"Workbook file not found: {file_path}"
            )

        # Load the workbook
        workbook = load_workbook_from_yaml(file_path)

        # Find the sheet
        sheet = None
        for s in workbook.sheets:
            if s.name == sheet_name:
                sheet = s
                break

        if not sheet:
            raise HTTPException(
                status_code=404, detail=f"Sheet '{sheet_name}' not found"
            )

        # Find the cell
        cell = None
        for c in sheet.cells:
            if c.id == cell_id:
                cell = c
                break

        if not cell:
            raise HTTPException(
                status_code=404,
                detail=f"Cell '{cell_id}' not found in sheet '{sheet_name}'",
            )

        return {
            "sheet_name": sheet_name,
            "cell_id": cell_id,
            "value": cell.value,
            "formula": cell.formula,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: Request, chat: ChatRequest = Body(...)):
    """Chat endpoint for LLM interaction with spreadsheet context."""
    # Load YAML file as context
    file_path = _get_workbook_file_path()
    if not file_path.exists():
        return ChatResponse(response="No spreadsheet found.")
    with open(file_path, "r", encoding="utf-8") as f:
        yaml_content = f.read()
    # Provide context to the LLM (mocked for now)
    context = {
        "yaml": yaml_content,
        "schema": SPREADSHEET_SCHEMA,
        "history": chat.history,
        "user_message": chat.message,
    }
    # Mock LLM: echo the message and suggest an update if asked
    if "update" in chat.message.lower():
        # Example: suggest updating A1 in Sheet1
        return ChatResponse(
            response="I suggest updating cell A1 in Sheet1 to value '42'. Do you want to apply this?",
            action="update_cell",
            action_args={"sheet_name": "Sheet1", "cell_id": "A1", "value": "42"},
        )
    return ChatResponse(response=f"You said: {chat.message}")


@router.get("/workbook/yaml", response_class=PlainTextResponse)
async def get_workbook_yaml():
    file_path = _get_workbook_file_path()
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Workbook file not found")
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


@router.put("/workbook/yaml")
async def update_workbook_yaml(yaml_content: str = Body(..., embed=True)):
    file_path = _get_workbook_file_path()
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Workbook file not found")
    try:
        data = yaml.safe_load(yaml_content)
        Workbook.model_validate(data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid YAML: {e}")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(yaml_content)
    return {"message": "YAML updated successfully"}


@router.get("/workbook/yaml-diff", response_class=PlainTextResponse)
async def get_yaml_diff():
    file_path = _get_workbook_file_path()
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Workbook file not found")
    try:
        result = subprocess.run(
            ["git", "diff", "--", str(file_path)],
            cwd=file_path.parent,
            capture_output=True,
            text=True,
            check=False,
        )
        diff = result.stdout
        if not diff:
            # If no diff, check if file is untracked
            status = subprocess.run(
                ["git", "ls-files", "--others", "--exclude-standard", str(file_path)],
                cwd=file_path.parent,
                capture_output=True,
                text=True,
                check=False,
            )
            if status.stdout.strip():
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                diff = f"--- /dev/null\n+++ b/{file_path.name}\n@@ ... @@\n{content}"
        return diff or "No changes"
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Git diff error: {e}")


@router.post("/workbook/commit")
async def commit_yaml_file(message: str = Body(..., embed=True)):
    file_path = _get_workbook_file_path()
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Workbook file not found")
    try:
        subprocess.run(
            ["git", "add", str(file_path)],
            cwd=file_path.parent,
            check=True,
        )
        subprocess.run(
            ["git", "commit", "-m", message],
            cwd=file_path.parent,
            check=True,
        )
        return {"message": "Committed successfully"}
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Git commit error: {e}")
