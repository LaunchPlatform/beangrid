import os
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List

from fastapi import APIRouter
from fastapi import HTTPException
from pydantic import BaseModel

from ..core.processor import FormulaProcessor
from ..core.yaml_processor import load_workbook_from_yaml
from ..core.yaml_processor import save_workbook_to_yaml
from ..scheme.cell import Cell
from ..scheme.cell import Workbook

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
    value: str = None
    formula: str = None


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
async def update_cell(request: CellUpdateRequest):
    """Update a cell in the workbook and save to YAML file."""
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
                    cell.value = request.value
                if request.formula is not None:
                    cell.formula = request.formula
                cell_updated = True
                break

        if not cell_updated:
            # Create new cell if it doesn't exist
            new_cell = Cell(
                id=request.cell_id, value=request.value, formula=request.formula
            )
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
