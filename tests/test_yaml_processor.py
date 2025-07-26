import tempfile
from pathlib import Path

import yaml

from beangrid.core.yaml_processor import create_sample_workbook
from beangrid.core.yaml_processor import load_workbook_from_yaml
from beangrid.core.yaml_processor import load_workbook_from_yaml_fileobj
from beangrid.core.yaml_processor import save_workbook_to_yaml
from beangrid.core.yaml_processor import save_workbook_to_yaml_fileobj


def test_create_sample_workbook():
    """Test creating a sample workbook."""
    workbook = create_sample_workbook()

    assert len(workbook.sheets) == 1
    assert workbook.sheets[0].name == "Sales"
    assert len(workbook.sheets[0].cells) == 16

    # Check some specific cells
    cell_dict = workbook.sheets[0].get_cell_dict()
    assert cell_dict["A1"].value == "Product"
    assert cell_dict["D2"].formula == "=B2*C2"
    assert cell_dict["D4"].formula == "=SUM(D2:D3)"


def test_save_and_load_workbook():
    """Test saving and loading a workbook from YAML."""
    workbook = create_sample_workbook()

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        temp_path = f.name

    try:
        # Save workbook to YAML
        save_workbook_to_yaml(workbook, temp_path)

        # Load workbook from YAML
        loaded_workbook = load_workbook_from_yaml(temp_path)

        # Verify the loaded workbook matches the original
        assert len(loaded_workbook.sheets) == len(workbook.sheets)
        assert loaded_workbook.sheets[0].name == workbook.sheets[0].name
        assert len(loaded_workbook.sheets[0].cells) == len(workbook.sheets[0].cells)

        # Check specific cells
        original_cells = {cell.id: cell for cell in workbook.sheets[0].cells}
        loaded_cells = {cell.id: cell for cell in loaded_workbook.sheets[0].cells}

        for cell_id in original_cells:
            assert cell_id in loaded_cells
            assert original_cells[cell_id].value == loaded_cells[cell_id].value
            assert original_cells[cell_id].formula == loaded_cells[cell_id].formula

    finally:
        # Clean up
        Path(temp_path).unlink(missing_ok=True)


def test_save_and_load_workbook_fileobj():
    """Test saving and loading a workbook using file objects."""
    workbook = create_sample_workbook()

    # Save to string buffer
    import io

    buffer = io.StringIO()
    save_workbook_to_yaml_fileobj(workbook, buffer)

    # Reset buffer position
    buffer.seek(0)

    # Load from string buffer
    loaded_workbook = load_workbook_from_yaml_fileobj(buffer)

    # Verify the loaded workbook matches the original
    assert len(loaded_workbook.sheets) == len(workbook.sheets)
    assert loaded_workbook.sheets[0].name == workbook.sheets[0].name


def test_yaml_format():
    """Test that the YAML output has the expected format."""
    workbook = create_sample_workbook()

    import io

    buffer = io.StringIO()
    save_workbook_to_yaml_fileobj(workbook, buffer)

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


if __name__ == "__main__":
    # Run tests
    test_create_sample_workbook()
    test_save_and_load_workbook()
    test_save_and_load_workbook_fileobj()
    test_yaml_format()
    print("All tests passed!")
