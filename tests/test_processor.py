import pytest

from beangrid.core.processor import FormulaProcessor
from beangrid.scheme.cell import Cell
from beangrid.scheme.cell import Sheet
from beangrid.scheme.cell import Workbook


def test_simple_formula_evaluation():
    """Test basic formula evaluation."""
    workbook = Workbook(
        sheets=[
            Sheet(
                name="Sheet1",
                cells=[
                    Cell(id="A1", value="10", formula=None),
                    Cell(id="A2", value="20", formula=None),
                    Cell(id="A3", value=None, formula="A1 + A2"),
                ],
            )
        ]
    )

    processor = FormulaProcessor()
    result = processor.process_workbook(workbook)

    # Check that A3 was calculated correctly
    cells = result.sheets[0].get_cell_dict()
    a3_cell = cells["A3"]
    assert a3_cell.value == "30.0"
    assert a3_cell.formula == "A1 + A2"


def test_function_evaluation():
    """Test function evaluation."""
    workbook = Workbook(
        sheets=[
            Sheet(
                name="Sheet1",
                cells=[
                    Cell(id="A1", value="10", formula=None),
                    Cell(id="A2", value="20", formula=None),
                    Cell(id="A3", value="30", formula=None),
                    Cell(id="A4", value=None, formula="SUM(A1:A3)"),
                ],
            )
        ]
    )

    processor = FormulaProcessor()
    result = processor.process_workbook(workbook)

    # Check that A4 was calculated correctly
    cells = result.sheets[0].get_cell_dict()
    a4_cell = cells["A4"]
    assert a4_cell.value == "60.0"


def test_dependency_order():
    """Test that cells are evaluated in dependency order."""
    workbook = Workbook(
        sheets=[
            Sheet(
                name="Sheet1",
                cells=[
                    Cell(id="A1", value="10", formula=None),
                    Cell(id="A2", value=None, formula="A1 * 2"),  # Depends on A1
                    Cell(id="A3", value=None, formula="A2 + 5"),  # Depends on A2
                ],
            )
        ]
    )

    processor = FormulaProcessor()
    result = processor.process_workbook(workbook)

    # Check that all cells were calculated correctly
    cells = result.sheets[0].get_cell_dict()
    a2_cell = cells["A2"]
    a3_cell = cells["A3"]

    assert a2_cell.value == "20.0"
    assert a3_cell.value == "25.0"


def test_circular_dependency_detection():
    """Test that circular dependencies are detected."""
    workbook = Workbook(
        sheets=[
            Sheet(
                name="Sheet1",
                cells=[
                    Cell(id="A1", value=None, formula="A2 + 1"),
                    Cell(id="A2", value=None, formula="A1 + 1"),
                ],
            )
        ]
    )

    processor = FormulaProcessor()

    with pytest.raises(ValueError, match="Circular dependencies detected"):
        processor.process_workbook(workbook)


def test_sheet_references():
    """Test cross-sheet cell references."""
    workbook = Workbook(
        sheets=[
            Sheet(
                name="Sheet1",
                cells=[
                    Cell(id="A1", value="100", formula=None),
                ],
            ),
            Sheet(
                name="Sheet2",
                cells=[
                    Cell(id="A1", value=None, formula="Sheet1!A1 * 2"),
                ],
            ),
        ]
    )

    processor = FormulaProcessor()
    result = processor.process_workbook(workbook)

    # Check that Sheet2!A1 was calculated correctly
    cells = result.sheets[1].get_cell_dict()
    sheet2_a1 = cells["A1"]
    assert sheet2_a1.value == "200.0"


def test_complex_formula():
    """Test complex formula with multiple operations."""
    workbook = Workbook(
        sheets=[
            Sheet(
                name="Sheet1",
                cells=[
                    Cell(id="A1", value="10", formula=None),
                    Cell(id="A2", value="20", formula=None),
                    Cell(id="A3", value="30", formula=None),
                    Cell(id="A4", value=None, formula="(A1 + A2) * A3 / 2"),
                ],
            )
        ]
    )

    processor = FormulaProcessor()
    result = processor.process_workbook(workbook)

    # Check that A4 was calculated correctly: (10 + 20) * 30 / 2 = 450
    cells = result.sheets[0].get_cell_dict()
    a4_cell = cells["A4"]
    assert a4_cell.value == "450.0"


def test_string_concatenation():
    """Test string concatenation."""
    workbook = Workbook(
        sheets=[
            Sheet(
                name="Sheet1",
                cells=[
                    Cell(id="A1", value="Hello", formula=None),
                    Cell(id="A2", value="World", formula=None),
                    Cell(id="A3", value=None, formula='A1 & " " & A2'),
                ],
            )
        ]
    )

    processor = FormulaProcessor()
    result = processor.process_workbook(workbook)

    # Check that A3 was calculated correctly
    cells = result.sheets[0].get_cell_dict()
    a3_cell = cells["A3"]
    assert a3_cell.value == "Hello World"


def test_comparison_operations():
    """Test comparison operations."""
    workbook = Workbook(
        sheets=[
            Sheet(
                name="Sheet1",
                cells=[
                    Cell(id="A1", value="10", formula=None),
                    Cell(id="A2", value="20", formula=None),
                    Cell(id="A3", value=None, formula="A1 < A2"),
                    Cell(id="A4", value=None, formula="A1 = A2"),
                ],
            )
        ]
    )

    processor = FormulaProcessor()
    result = processor.process_workbook(workbook)

    # Check that comparisons work correctly
    cells = result.sheets[0].get_cell_dict()
    a3_cell = cells["A3"]
    a4_cell = cells["A4"]

    assert a3_cell.value == "True"
    assert a4_cell.value == "False"


def test_if_function():
    """Test IF function."""
    workbook = Workbook(
        sheets=[
            Sheet(
                name="Sheet1",
                cells=[
                    Cell(id="A1", value="10", formula=None),
                    Cell(id="A2", value=None, formula='IF(A1 > 5, "Yes", "No")'),
                    Cell(id="A3", value=None, formula='IF(A1 < 5, "Yes", "No")'),
                ],
            )
        ]
    )

    processor = FormulaProcessor()
    result = processor.process_workbook(workbook)

    # Check that IF function works correctly
    cells = result.sheets[0].get_cell_dict()
    a2_cell = cells["A2"]
    a3_cell = cells["A3"]

    assert a2_cell.value == "Yes"
    assert a3_cell.value == "No"


def test_error_handling():
    """Test error handling for invalid formulas."""
    workbook = Workbook(
        sheets=[
            Sheet(
                name="Sheet1",
                cells=[
                    Cell(id="A1", value="10", formula=None),
                    Cell(id="A2", value=None, formula="A1 / 0"),  # Division by zero
                    Cell(
                        id="A3", value=None, formula="INVALID_FUNCTION()"
                    ),  # Unknown function
                ],
            )
        ]
    )

    processor = FormulaProcessor()
    result = processor.process_workbook(workbook)

    # Check that errors are handled gracefully
    cells = result.sheets[0].get_cell_dict()
    a2_cell = cells["A2"]
    a3_cell = cells["A3"]

    assert "#DIV/0!" in a2_cell.value
    assert "#NAME?" in a3_cell.value
