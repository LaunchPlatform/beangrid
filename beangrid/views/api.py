import json
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
from fastapi import WebSocket
from fastapi import WebSocketDisconnect
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


class WorkbookUpdateRequest(BaseModel):
    """Request model for updating the entire workbook."""

    yaml_content: str
    commit_message: str


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
async def get_workbook(file_path: deps.YAMLFilePathDeps):
    """Get workbook data from the file specified by workdir."""
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
async def get_raw_workbook(file_path: deps.YAMLFilePathDeps):
    """Get raw workbook data without processing formulas."""
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
            f"{json.dumps(SPREADSHEET_SCHEMA, indent=2)}\n\n"
            "Answer the user's questions or suggest spreadsheet updates as needed. "
            "You can suggest actions in two ways:\n"
            '1. For cell updates: {"action": "update_cell", "action_args": {"sheet_name": "Sheet1", "cell_id": "A1", "value": "New Value"}}\n'
            '2. For full workbook updates: {"action": "update_workbook", "action_args": {"yaml_content": "complete yaml content here", "commit_message": "Description of changes"}}\n'
            "When suggesting workbook updates, provide the complete YAML content (not just the changes) and a clear commit message describing what was changed. "
            "The yaml_content should be the full workbook YAML, not just the modified parts."
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
        with chat_file.open("r", encoding="utf-8") as f:
            history = [json.loads(line) for line in f if line.strip()]

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
            action_json = json.loads(match.group(0))
            action = action_json.get("action")
            action_args = action_json.get("action_args")
        except Exception:
            pass

    return ChatResponse(response=llm_reply, action=action, action_args=action_args)


@router.get("/chat/history")
async def get_chat_history(chat_file: deps.ChatFileDeps):
    """Get chat history from the JSONL file."""
    try:
        if not chat_file.exists():
            return []

        messages = []
        with chat_file.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        message = json.loads(line)
                        messages.append(message)
                    except json.JSONDecodeError:
                        continue

        return messages
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load chat history: {e}")


@router.websocket("/chat/ws")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    yaml_content: deps.YAMLContentWebSocketDeps,
    chat_file: deps.ChatFileWebSocketDeps,
):
    """WebSocket endpoint for real-time chat with streaming support."""
    await websocket.accept()

    try:
        # Initialize chat history similar to the HTTP endpoint
        if not chat_file.exists():
            static_system_prompt = (
                "You are a helpful spreadsheet assistant. "
                "The user is working with a spreadsheet in YAML format. "
                "Here is the JSON schema for the spreadsheet:\n"
                f"{json.dumps(SPREADSHEET_SCHEMA, indent=2)}\n\n"
                "Answer the user's questions or suggest spreadsheet updates as needed. "
                "You can suggest actions in two ways:\n"
                '1. For cell updates: {"action": "update_cell", "action_args": {"sheet_name": "Sheet1", "cell_id": "A1", "value": "New Value"}}\n'
                '2. For full workbook updates: {"action": "update_workbook", "action_args": {"yaml_content": "complete yaml content here", "commit_message": "Description of changes"}}\n'
                "When suggesting workbook updates, provide the complete YAML content (not just the changes) and a clear commit message describing what was changed. "
                "The yaml_content should be the full workbook YAML, not just the modified parts.\n\n"
                "IMPORTANT: When you need to think through a problem or analyze the spreadsheet, "
                "enclose your thinking process between <think> and </think> tags. "
                "This helps users understand your reasoning process. "
                "For example:\n"
                "<think>\n"
                "Let me analyze the current spreadsheet structure...\n"
                "I need to check what data is available...\n"
                "</think>\n"
                "Then provide your final answer or recommendation."
            )
            yaml_system_message = {
                "role": "system",
                "content": f"Current spreadsheet YAML content:\n{yaml_content}",
            }
            history = [
                {"role": "system", "content": static_system_prompt},
                yaml_system_message,
            ]
            with chat_file.open("w", encoding="utf-8") as f:
                for msg in history:
                    f.write(json.dumps(msg, ensure_ascii=False) + "\n")
        else:
            with chat_file.open("r", encoding="utf-8") as f:
                history = [json.loads(line) for line in f if line.strip()]

        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            user_message = message_data.get("message", "")

            # Append user message to history
            user_msg = {"role": "user", "content": user_message}
            messages = history + [user_msg]

            # Write user message to chat file
            with chat_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(user_msg, ensure_ascii=False) + "\n")

            # Send thinking indicator
            await websocket.send_text(
                json.dumps({"type": "thinking", "content": "🤔 Thinking..."})
            )

            # Stream the LLM response
            try:
                response = await litellm.acompletion(
                    model="ollama/deepseek-r1:32b",
                    messages=messages,
                    stream=True,
                    api_base="http://192.168.50.71:11434",
                )

                full_response = ""
                thinking_content = ""
                in_thinking_block = False
                thinking_complete = False
                current_thinking_content = ""

                async for chunk in response:
                    if chunk and "choices" in chunk and len(chunk["choices"]) > 0:
                        delta = chunk["choices"][0].get("delta", {})
                        if "content" in delta and delta["content"]:
                            content = delta["content"]
                            full_response += content

                            # Check for thinking blocks
                            if "<think>" in content:
                                in_thinking_block = True
                                # Remove the <think> tag from content before sending
                                content = content.replace("<think>", "")
                                # Send thinking start indicator
                                await websocket.send_text(
                                    json.dumps(
                                        {"type": "thinking_start", "content": ""}
                                    )
                                )

                            if in_thinking_block:
                                thinking_content += content
                                # Send thinking content in real-time (without tags)
                                await websocket.send_text(
                                    json.dumps(
                                        {"type": "thinking_stream", "content": content}
                                    )
                                )

                            if "</think>" in content:
                                in_thinking_block = False
                                thinking_complete = True
                                # Remove the </think> tag from content
                                content = content.replace("</think>", "")
                                # Send thinking end indicator
                                await websocket.send_text(
                                    json.dumps({"type": "thinking_end", "content": ""})
                                )

                            # Only send regular stream content if not in thinking block and content is not empty
                            if not in_thinking_block and content.strip():
                                await websocket.send_text(
                                    json.dumps({"type": "stream", "content": content})
                                )

                # Clean the response by removing thinking tags for chat history
                cleaned_response = re.sub(
                    r"<think>.*?</think>", "", full_response, flags=re.DOTALL
                ).strip()

                # Write assistant message to chat file (without thinking tags)
                assistant_message = {"role": "assistant", "content": cleaned_response}
                with chat_file.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(assistant_message, ensure_ascii=False) + "\n")

                # Try to extract action from response
                action = None
                action_args = None
                match = re.search(
                    r'\{\s*"action"\s*:\s*"[^"]+".*\}', full_response, re.DOTALL
                )
                if match:
                    try:
                        action_json = json.loads(match.group(0))
                        action = action_json.get("action")
                        action_args = action_json.get("action_args")
                    except Exception:
                        pass

                # Send completion signal with action info
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "complete",
                            "action": action,
                            "action_args": action_args,
                        }
                    )
                )

            except Exception as e:
                await websocket.send_text(
                    json.dumps({"type": "error", "content": f"LLM error: {e}"})
                )

    except WebSocketDisconnect:
        print("WebSocket client disconnected")
    except Exception as e:
        await websocket.send_text(
            json.dumps({"type": "error", "content": f"WebSocket error: {e}"})
        )


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
async def get_yaml_diff(workdir: deps.WorkdirDeps):
    try:
        workbook_file = workdir / "workbook.yaml"
        result = subprocess.run(
            ["git", "diff", "--", str(workbook_file)],
            cwd=workdir,
            capture_output=True,
            text=True,
            check=False,
        )
        diff = result.stdout
        if not diff:
            # If no diff, check if file is untracked
            status = subprocess.run(
                [
                    "git",
                    "ls-files",
                    "--others",
                    "--exclude-standard",
                    str(workbook_file),
                ],
                cwd=workdir,
                capture_output=True,
                text=True,
                check=False,
            )
            if status.stdout.strip():
                with open(workbook_file, "r", encoding="utf-8") as f:
                    content = f.read()
                diff = (
                    f"--- /dev/null\n+++ b/{workbook_file.name}\n@@ ... @@\n{content}"
                )
        return diff or "No changes"
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Git diff error: {e}")


@router.post("/workbook/commit")
async def commit_yaml_file(
    workdir: deps.WorkdirDeps, message: str = Body(..., embed=True)
):
    try:
        workbook_file = workdir / "workbook.yaml"
        subprocess.run(
            ["git", "add", str(workbook_file)],
            cwd=workdir,
            check=True,
        )
        subprocess.run(
            ["git", "commit", "-m", message],
            cwd=workdir,
            check=True,
        )
        return {"message": "Committed successfully"}
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Git commit error: {e}")
