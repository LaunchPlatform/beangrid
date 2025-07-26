import tempfile
from pathlib import Path

import pytest
import yaml

from beangrid.core.yaml_processor import load_workbook_from_yaml
from beangrid.core.yaml_processor import load_workbook_from_yaml_fileobj
from beangrid.core.yaml_processor import save_workbook_to_yaml
from beangrid.core.yaml_processor import save_workbook_to_yaml_fileobj
from beangrid.scheme.cell import Workbook


@pytest.fixture
def sample_workbook() -> Workbook:
    """Load sample workbook from fixtures."""
    fixture_path = Path(__file__).parent / "fixtures" / "sample_workbook.yaml"
    return load_workbook_from_yaml(fixture_path)


@pytest.fixture
def multi_sheet_workbook() -> Workbook:
    """Load multi-sheet workbook from fixtures."""
    fixture_path = Path(__file__).parent / "fixtures" / "multi_sheet_workbook.yaml"
    return load_workbook_from_yaml(fixture_path)


def test_sample_workbook(sample_workbook: Workbook):
    """Test loading sample workbook from fixture."""
    assert len(sample_workbook.sheets) == 1
    assert sample_workbook.sheets[0].name == "Sales"
    assert len(sample_workbook.sheets[0].cells) == 16

    # Check some specific cells
    cell_dict = sample_workbook.sheets[0].get_cell_dict()
    assert cell_dict["A1"].value == "Product"
    assert cell_dict["D2"].formula == "=B2*C2"
    assert cell_dict["D4"].formula == "=SUM(D2:D3)"


def test_save_and_load_workbook(sample_workbook: Workbook, tmp_path: Path):
    """Test saving and loading a workbook from YAML."""
    temp_path = tmp_path / "workbook.yaml"

    # Save workbook to YAML
    save_workbook_to_yaml(sample_workbook, temp_path)

    # Load workbook from YAML
    loaded_workbook = load_workbook_from_yaml(temp_path)

    # Verify the loaded workbook matches the original
    assert len(loaded_workbook.sheets) == len(sample_workbook.sheets)
    assert loaded_workbook.sheets[0].name == sample_workbook.sheets[0].name
    assert len(loaded_workbook.sheets[0].cells) == len(sample_workbook.sheets[0].cells)

    # Check specific cells
    original_cells = {cell.id: cell for cell in sample_workbook.sheets[0].cells}
    loaded_cells = {cell.id: cell for cell in loaded_workbook.sheets[0].cells}

    for cell_id in original_cells:
        assert cell_id in loaded_cells
        assert original_cells[cell_id].value == loaded_cells[cell_id].value
        assert original_cells[cell_id].formula == loaded_cells[cell_id].formula


def test_save_and_load_workbook_fileobj(sample_workbook: Workbook):
    """Test saving and loading a workbook using file objects."""
    # Save to string buffer
    import io

    buffer = io.StringIO()
    save_workbook_to_yaml_fileobj(sample_workbook, buffer)

    # Reset buffer position
    buffer.seek(0)

    # Load from string buffer
    loaded_workbook = load_workbook_from_yaml_fileobj(buffer)

    # Verify the loaded workbook matches the original
    assert len(loaded_workbook.sheets) == len(sample_workbook.sheets)
    assert loaded_workbook.sheets[0].name == sample_workbook.sheets[0].name


def test_yaml_format(sample_workbook: Workbook):
    """Test that the YAML output has the expected format."""
    import io

    buffer = io.StringIO()
    save_workbook_to_yaml_fileobj(sample_workbook, buffer)

    yaml_content = buffer.getvalue()

    # Verify YAML structure
    data = yaml.safe_load(yaml_content)
    assert "sheets" in data
    assert len(data["sheets"]) == 1
    assert data["sheets"][0]["name"] == "Sales"
    assert len(data["sheets"][0]["cells"]) == 16

    # Check specific cell format
    cells = {cell["id"]: cell for cell in data["sheets"][0]["cells"]}
    assert cells["A1"]["value"] == "Product"
    assert cells["D2"]["formula"] == "=B2*C2"
    assert "value" not in cells["D2"]  # Should not have value if it's a formula cell


def test_multi_sheet_workbook(multi_sheet_workbook: Workbook):
    """Test loading multi-sheet workbook from fixture."""
    assert len(multi_sheet_workbook.sheets) == 2
    assert multi_sheet_workbook.sheets[0].name == "Sales"
    assert multi_sheet_workbook.sheets[1].name == "Summary"

    # Check Sales sheet
    sales_cells = {cell.id: cell for cell in multi_sheet_workbook.sheets[0].cells}
    assert sales_cells["A1"].value == "Product"
    assert sales_cells["D2"].formula == "=B2*C2"
    assert sales_cells["D4"].formula == "=SUM(D2:D3)"

    # Check Summary sheet
    summary_cells = {cell.id: cell for cell in multi_sheet_workbook.sheets[1].cells}
    assert summary_cells["A1"].value == "Summary Report"
    assert summary_cells["B2"].formula == "=Sales!D4"
    assert summary_cells["B3"].formula == "=AVERAGE(Sales!B2:B3)"
    assert summary_cells["B4"].formula == "=SUM(Sales!C2:C3)"
