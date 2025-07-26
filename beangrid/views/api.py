import json as _json
import os
import re
import subprocess
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List

import litellm
import yaml
from fastapi import APIRouter
from fastapi import Body
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from .. import deps
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


@router.put("/workbook/cell")
async def update_cell(
    file_path: deps.YAMLFilePathDeps, request: CellUpdateRequest = Body(...)
):
    """Update a cell in the workbook and save to YAML file."""
    print(f"Received cell update request: {request}")
    try:
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
async def get_cell(file_path: deps.YAMLFilePathDeps, sheet_name: str, cell_id: str):
    """Get a specific cell from the workbook."""
    try:
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
async def chat_endpoint(
    request: Request,
    yaml_content: deps.YAMLContentDeps,
    workdir: deps.WorkdirDeps,
    chat_file: deps.ChatFileDeps,
    chat: ChatRequest = Body(...),
):
    """Chat endpoint for LLM interaction with spreadsheet context using litellm and persistent chat history."""

    # 1. Check if chat file exists, if not create it and insert system prompts
    if not chat_file.exists():
        static_system_prompt = (
            "You are a helpful spreadsheet assistant. "
            "The user is working with a spreadsheet in YAML format. "
            "Here is the JSON schema for the spreadsheet:\n"
            f"{_json.dumps(SPREADSHEET_SCHEMA, indent=2)}\n\n"
            "Answer the user's questions or suggest spreadsheet updates as needed. "
            'If you want to suggest an action, respond with a JSON object like: {"action": "update_cell", "action_args": { ... }}. '
            "Otherwise, just answer in plain text."
        )
        yaml_system_message = {
            "role": "system",
            "content": f"Current spreadsheet YAML content:\n{yaml_content}",
        }
        # Initialize history with system prompts
        history = [
            {"role": "system", "content": static_system_prompt},
            yaml_system_message,
        ]
        # Write system prompts to file
        with chat_file.open("w", encoding="utf-8") as f:
            for msg in history:
                f.write(json.dumps(msg, ensure_ascii=False) + "\n")
    else:
        # 2. If chat file exists, read messages into history variable
        history = []
        with chat_file.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    history.append(json.loads(line))

    # 3. Append user chat message to messages and write to chat file
    user_message = {"role": "user", "content": chat.message}
    messages = history + [user_message]

    # Write user message to chat file
    with chat_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(user_message, ensure_ascii=False) + "\n")

    # 4. Submit messages to LLM using litellm
    try:
        response = await litellm.acompletion(
            model="ollama/deepseek-r1:32b",
            messages=messages,
            stream=False,
            api_base="http://192.168.50.71:11434",
        )
        llm_reply = response["choices"][0]["message"]["content"]
    except Exception as e:
        return ChatResponse(response=f"LLM error: {e}")

    # 5. Write LLM reply to chat file
    assistant_message = {"role": "assistant", "content": llm_reply}
    with chat_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(assistant_message, ensure_ascii=False) + "\n")

    # Try to extract action from LLM reply if present
    action = None
    action_args = None
    match = re.search(r'\{\s*"action"\s*:\s*"[^"]+".*\}', llm_reply, re.DOTALL)
    if match:
        try:
            action_json = _json.loads(match.group(0))
            action = action_json.get("action")
            action_args = action_json.get("action_args")
        except Exception:
            pass

    return ChatResponse(response=llm_reply, action=action, action_args=action_args)


@router.get("/workbook/yaml", response_class=PlainTextResponse)
async def get_workbook_yaml(yaml_content: deps.YAMLContentDeps):
    return yaml_content


@router.put("/workbook/yaml")
async def update_workbook_yaml(
    file_path: deps.YAMLFilePathDeps, yaml_content: str = Body(..., embed=True)
):
    try:
        data = yaml.safe_load(yaml_content)
        Workbook.model_validate(data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid YAML: {e}")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(yaml_content)
    return {"message": "YAML updated successfully"}


@router.get("/workbook/yaml-diff", response_class=PlainTextResponse)
async def get_yaml_diff(file_path: deps.YAMLFilePathDeps):
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
async def commit_yaml_file(
    file_path: deps.YAMLFilePathDeps, message: str = Body(..., embed=True)
):
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
