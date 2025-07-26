from pathlib import Path
from typing import Any
from typing import Dict
from typing import Optional
from typing import TextIO
from typing import Union

import yaml

from ..scheme.cell import Cell
from ..scheme.cell import Sheet
from ..scheme.cell import Workbook


def load_workbook_from_yaml(file_path: Union[str, Path]) -> Workbook:
    """
    Load a Workbook from a YAML file.

    Args:
        file_path: Path to the YAML file

    Returns:
        Workbook object loaded from the YAML file

    Raises:
        FileNotFoundError: If the file doesn't exist
        yaml.YAMLError: If the YAML is malformed
        ValueError: If the YAML structure doesn't match expected Workbook format
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"YAML file not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        return load_workbook_from_yaml_fileobj(f)


def load_workbook_from_yaml_fileobj(fileobj: TextIO) -> Workbook:
    """
    Load a Workbook from a file-like object containing YAML.

    Args:
        fileobj: File-like object containing YAML data

    Returns:
        Workbook object loaded from the YAML data

    Raises:
        yaml.YAMLError: If the YAML is malformed
        ValueError: If the YAML structure doesn't match expected Workbook format
    """
    try:
        data = yaml.safe_load(fileobj)
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Failed to parse YAML: {e}")

    return _dict_to_workbook(data)


def save_workbook_to_yaml(workbook: Workbook, file_path: Union[str, Path]) -> None:
    """
    Save a Workbook to a YAML file.

    Args:
        workbook: Workbook object to save
        file_path: Path where to save the YAML file

    Raises:
        OSError: If the file cannot be written
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, "w", encoding="utf-8") as f:
        save_workbook_to_yaml_fileobj(workbook, f)


def save_workbook_to_yaml_fileobj(workbook: Workbook, fileobj: TextIO) -> None:
    """
    Save a Workbook to a file-like object in YAML format.

    Args:
        workbook: Workbook object to save
        fileobj: File-like object to write YAML data to
    """
    data = _workbook_to_dict(workbook)
    yaml.dump(data, fileobj, default_flow_style=False, sort_keys=False)


def _dict_to_workbook(data: Dict[str, Any]) -> Workbook:
    """
    Convert a dictionary to a Workbook object.

    Args:
        data: Dictionary containing workbook data

    Returns:
        Workbook object

    Raises:
        ValueError: If the data structure doesn't match expected format
    """
    if not isinstance(data, dict):
        raise ValueError("Expected dictionary for workbook data")

    if "sheets" not in data:
        raise ValueError("Workbook data must contain 'sheets' key")

    sheets_data = data["sheets"]
    if not isinstance(sheets_data, list):
        raise ValueError("'sheets' must be a list")

    sheets = []
    for i, sheet_data in enumerate(sheets_data):
        if not isinstance(sheet_data, dict):
            raise ValueError(f"Sheet {i} must be a dictionary")

        if "name" not in sheet_data:
            raise ValueError(f"Sheet {i} must have a 'name' field")

        if "cells" not in sheet_data:
            raise ValueError(f"Sheet {i} must have a 'cells' field")

        cells_data = sheet_data["cells"]
        if not isinstance(cells_data, list):
            raise ValueError(f"Sheet {i} 'cells' must be a list")

        cells = []
        for j, cell_data in enumerate(cells_data):
            if not isinstance(cell_data, dict):
                raise ValueError(f"Cell {j} in sheet {i} must be a dictionary")

            if "id" not in cell_data:
                raise ValueError(f"Cell {j} in sheet {i} must have an 'id' field")

            cell = Cell(
                id=cell_data["id"],
                value=cell_data.get("value"),
                formula=cell_data.get("formula"),
            )
            cells.append(cell)

        sheet = Sheet(name=sheet_data["name"], cells=cells)
        sheets.append(sheet)

    return Workbook(sheets=sheets)


def _workbook_to_dict(workbook: Workbook) -> Dict[str, Any]:
    """
    Convert a Workbook object to a dictionary.

    Args:
        workbook: Workbook object to convert

    Returns:
        Dictionary representation of the workbook
    """
    sheets_data = []
    for sheet in workbook.sheets:
        cells_data = []
        for cell in sheet.cells:
            cell_data = {"id": cell.id}
            if cell.value is not None:
                cell_data["value"] = cell.value
            if cell.formula is not None:
                cell_data["formula"] = cell.formula
            cells_data.append(cell_data)

        sheet_data = {"name": sheet.name, "cells": cells_data}
        sheets_data.append(sheet_data)

    return {"sheets": sheets_data}


def create_sample_workbook() -> Workbook:
    """
    Create a sample workbook for testing purposes.

    Returns:
        A sample Workbook with some example data
    """
    cells = [
        Cell(id="A1", value="Product", formula=None),
        Cell(id="B1", value="Price", formula=None),
        Cell(id="C1", value="Quantity", formula=None),
        Cell(id="D1", value="Total", formula=None),
        Cell(id="A2", value="Apple", formula=None),
        Cell(id="B2", value="1.50", formula=None),
        Cell(id="C2", value="10", formula=None),
        Cell(id="D2", value=None, formula="=B2*C2"),
        Cell(id="A3", value="Banana", formula=None),
        Cell(id="B3", value="0.75", formula=None),
        Cell(id="C3", value="15", formula=None),
        Cell(id="D3", value=None, formula="=B3*C3"),
        Cell(id="A4", value="Total", formula=None),
        Cell(id="B4", value=None, formula=None),
        Cell(id="C4", value=None, formula=None),
        Cell(id="D4", value=None, formula="=SUM(D2:D3)"),
    ]

    sheet = Sheet(name="Sales", cells=cells)
    return Workbook(sheets=[sheet])
