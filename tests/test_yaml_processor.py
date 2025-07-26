import tempfile
from pathlib import Path

import pytest
import yaml

from beangrid.core.processor import FormulaProcessor
from beangrid.core.yaml_processor import load_workbook_from_yaml
from beangrid.core.yaml_processor import load_workbook_from_yaml_fileobj
from beangrid.core.yaml_processor import save_workbook_to_yaml
from beangrid.core.yaml_processor import save_workbook_to_yaml_fileobj
from beangrid.scheme.cell import Workbook


@pytest.fixture
def fixtures_folder() -> Path:
    """Get the fixtures folder path."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_workbook(fixtures_folder: Path) -> Workbook:
    """Load sample workbook from fixtures."""
    fixture_path = fixtures_folder / "sample_workbook.yaml"
    return load_workbook_from_yaml(fixture_path)


@pytest.fixture
def multi_sheet_workbook(fixtures_folder: Path) -> Workbook:
    """Load multi-sheet workbook from fixtures."""
    fixture_path = fixtures_folder / "multi_sheet_workbook.yaml"
    return load_workbook_from_yaml(fixture_path)


@pytest.fixture
def simple_calculations_workbook(fixtures_folder: Path) -> Workbook:
    """Load simple calculations workbook from fixtures."""
    fixture_path = fixtures_folder / "simple_calculations.yaml"
    return load_workbook_from_yaml(fixture_path)


@pytest.fixture
def function_tests_workbook(fixtures_folder: Path) -> Workbook:
    """Load function tests workbook from fixtures."""
    fixture_path = fixtures_folder / "function_tests.yaml"
    return load_workbook_from_yaml(fixture_path)


@pytest.fixture
def cross_sheet_references_workbook(fixtures_folder: Path) -> Workbook:
    """Load cross-sheet references workbook from fixtures."""
    fixture_path = fixtures_folder / "cross_sheet_references.yaml"
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


@pytest.mark.parametrize(
    "workbook_fixture,expected_results",
    [
        (
            "simple_calculations_workbook",
            {
                "Calculations": {
                    "C1": "30.0",  # 10 + 20
                    "C2": "15.0",  # 5 * 3
                    "C3": "25.0",  # 100 / 4
                    "B4": "225.0",  # 15^2
                }
            },
        ),
        (
            "function_tests_workbook",
            {
                "Functions": {
                    "B1": "100.0",  # SUM(A1:A4) = 10+20+30+40
                    "B2": "25.0",  # AVERAGE(A1:A4) = (10+20+30+40)/4
                    "B3": "40.0",  # MAX(A1:A4)
                    "B4": "10.0",  # MIN(A1:A4)
                    "D1": "4.0",  # COUNT(A1:A4)
                    "D2": "3.0",  # COUNTA(C1:C3)
                }
            },
        ),
        (
            "cross_sheet_references_workbook",
            {
                "Summary": {
                    "B1": "325.0",  # SUM(Data!B2:B4) = 100+150+75
                    "B2": "108.3",  # AVERAGE(Data!B2:B4) = (100+150+75)/3
                    "B3": "150.0",  # MAX(Data!B2:B4)
                    "B4": "75.0",  # MIN(Data!B2:B4)
                }
            },
        ),
        (
            "sample_workbook",
            {
                "Sales": {
                    "D2": "15.0",  # 1.50 * 10
                    "D3": "11.2",  # 0.75 * 15
                    "D4": "26.2",  # SUM(D2:D3)
                }
            },
        ),
    ],
)
def test_formula_evaluation(workbook_fixture: str, expected_results: dict, request):
    """Test formula evaluation using the processor with parameterized test cases."""
    # Get the workbook fixture dynamically
    workbook = request.getfixturevalue(workbook_fixture)

    # Process the workbook with formulas
    processor = FormulaProcessor()
    processed_workbook = processor.process_workbook(workbook)

    # Check each expected result
    for sheet_name, cell_results in expected_results.items():
        # Find the sheet
        sheet = next(
            (s for s in processed_workbook.sheets if s.name == sheet_name), None
        )
        assert sheet is not None, f"Sheet '{sheet_name}' not found"

        # Create cell lookup dictionary
        cell_dict = sheet.get_cell_dict()

        # Check each cell result
        for cell_id, expected_value in cell_results.items():
            cell = cell_dict.get(cell_id)
            assert cell is not None, (
                f"Cell '{cell_id}' not found in sheet '{sheet_name}'"
            )
            assert cell.value == expected_value, (
                f"Expected {cell_id}={expected_value}, got {cell.value}"
            )
