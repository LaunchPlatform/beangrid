import pytest

from beangrid.core.parser import parse_excel_formula


@pytest.mark.parametrize(
    "formula, expected_repr",
    [
        # Simple number
        ("42", "Number(42.0)"),
        # Simple string
        ('"hello"', "String('hello')"),
        # Boolean TRUE
        ("TRUE", "Bool(True)"),
        # Boolean FALSE
        ("FALSE", "Bool(False)"),
        # Simple cell reference
        ("A1", "Cell('A1')"),
        # Cell reference with sheet
        ("Sheet1!B2", "Cell('B2', sheet='Sheet1')"),
        # Cell range
        ("A1:B2", "CellRange(Cell('A1'), Cell('B2'))"),
        # Function call with one argument
        ("SUM(A1)", "FuncCall('SUM', [Cell('A1')])"),
        # Function call with multiple arguments
        ("SUM(A1, 2, 3)", "FuncCall('SUM', [Cell('A1'), Number(2.0), Number(3.0)])"),
        # Nested function call
        (
            "SUM(AVERAGE(A1:A3), 10)",
            "FuncCall('SUM', [FuncCall('AVERAGE', [CellRange(Cell('A1'), Cell('A3'))]), Number(10.0)])",
        ),
        # Binary operation
        ("A1 + 2", "BinOp(Cell('A1'), '+', Number(2.0))"),
        # Multiple binary operations
        ("A1 + B2 * 3", "BinOp(Cell('A1'), '+', BinOp(Cell('B2'), '*', Number(3.0)))"),
        # Parentheses
        (
            "(A1 + B2) * 3",
            "BinOp(BinOp(Cell('A1'), '+', Cell('B2')), '*', Number(3.0))",
        ),
        # Unary minus
        ("-A1", "UnaryOp('-', Cell('A1'))"),
        # Unary plus
        ("+A1", "UnaryOp('+', Cell('A1'))"),
        # Comparison
        ("A1 = B2", "BinOp(Cell('A1'), '=', Cell('B2'))"),
        # String concatenation
        ('"foo" & "bar"', "BinOp(String('foo'), '&', String('bar'))"),
        # Complex formula
        (
            'IF(A1>0, "Yes", "No")',
            "FuncCall('IF', [BinOp(Cell('A1'), '>', Number(0.0)), String('Yes'), String('No')])",
        ),
    ],
)
def test_parse_excel_formula(formula: str, expected_repr: str):
    ast = parse_excel_formula(formula)
    assert repr(ast) == expected_repr
