import pytest

from beangrid.core.parser import BinOp
from beangrid.core.parser import Bool
from beangrid.core.parser import Cell
from beangrid.core.parser import CellRange
from beangrid.core.parser import FuncCall
from beangrid.core.parser import Number
from beangrid.core.parser import parse_excel_formula
from beangrid.core.parser import String
from beangrid.core.parser import UnaryOp


@pytest.mark.parametrize(
    "formula, expected_ast",
    [
        # Simple number
        ("42", Number("42")),
        # Simple string
        ('"hello"', String('"hello"')),
        # Boolean TRUE
        ("TRUE", Bool("TRUE")),
        # Boolean FALSE
        ("FALSE", Bool("FALSE")),
        # Simple cell reference
        ("A1", Cell("A1")),
        # Cell reference with sheet
        ("Sheet1!B2", Cell("B2", sheet="Sheet1")),
        # Cell range
        ("A1:B2", CellRange(Cell("A1"), Cell("B2"))),
        # Function call with one argument
        ("SUM(A1)", FuncCall("SUM", [Cell("A1")])),
        # Function call with multiple arguments
        ("SUM(A1, 2, 3)", FuncCall("SUM", [Cell("A1"), Number("2"), Number("3")])),
        # Nested function call
        (
            "SUM(AVERAGE(A1:A3), 10)",
            FuncCall(
                "SUM",
                [
                    FuncCall("AVERAGE", [CellRange(Cell("A1"), Cell("A3"))]),
                    Number("10"),
                ],
            ),
        ),
        # Binary operation
        ("A1 + 2", BinOp(Cell("A1"), "+", Number("2"))),
        # Multiple binary operations
        ("A1 + B2 * 3", BinOp(Cell("A1"), "+", BinOp(Cell("B2"), "*", Number("3")))),
        # Parentheses
        (
            "(A1 + B2) * 3",
            BinOp(BinOp(Cell("A1"), "+", Cell("B2")), "*", Number("3")),
        ),
        # Unary minus
        ("-A1", UnaryOp("-", Cell("A1"))),
        # Unary plus
        ("+A1", UnaryOp("+", Cell("A1"))),
        # Comparison
        ("A1 = B2", BinOp(Cell("A1"), "=", Cell("B2"))),
        # String concatenation
        ('"foo" & "bar"', BinOp(String('"foo"'), "&", String('"bar"'))),
        # Complex formula
        (
            'IF(A1>0, "Yes", "No")',
            FuncCall(
                "IF",
                [
                    BinOp(Cell("A1"), ">", Number("0")),
                    String('"Yes"'),
                    String('"No"'),
                ],
            ),
        ),
    ],
)
def test_parse_excel_formula(formula: str, expected_ast):
    ast = parse_excel_formula(formula)
    assert repr(ast) == repr(expected_ast)
