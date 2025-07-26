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
from ..scheme.cell import Workbook

router = APIRouter(prefix="/api/v1")


class WorkbookResponse(BaseModel):
    """Response model for workbook data."""

    sheets: List[Dict[str, Any]]
    processed: bool
    error: str = None


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
