from typing import List
from typing import Optional


class ExcelAST:
    pass


class Number(ExcelAST):
    def __init__(self, value: str) -> None:
        self.value: float = float(value)

    def __repr__(self) -> str:
        return f"Number({self.value})"


class String(ExcelAST):
    def __init__(self, value: str) -> None:
        # Remove surrounding quotes and unescape double quotes
        self.value: str = value[1:-1].replace('""', '"')

    def __repr__(self) -> str:
        return f"String({self.value!r})"


class Bool(ExcelAST):
    def __init__(self, value: str) -> None:
        self.value: bool = value.upper() == "TRUE"

    def __repr__(self) -> str:
        return f"Bool({self.value})"


class Cell(ExcelAST):
    def __init__(self, ref: str, sheet: Optional[str] = None) -> None:
        self.ref: str = ref
        self.sheet: Optional[str] = sheet

    def __repr__(self) -> str:
        if self.sheet:
            return f"Cell({self.ref!r}, sheet={self.sheet!r})"
        return f"Cell({self.ref!r})"


class CellRange(ExcelAST):
    def __init__(self, start: Cell, end: Cell) -> None:
        self.start: Cell = start
        self.end: Cell = end

    def __repr__(self) -> str:
        return f"CellRange({self.start!r}, {self.end!r})"


class FuncCall(ExcelAST):
    def __init__(self, name: str, args: List[ExcelAST]) -> None:
        self.name: str = name
        self.args: List[ExcelAST] = args

    def __repr__(self) -> str:
        return f"FuncCall({self.name!r}, {self.args!r})"


class BinOp(ExcelAST):
    def __init__(self, left: ExcelAST, op: str, right: ExcelAST) -> None:
        self.left: ExcelAST = left
        self.op: str = op
        self.right: ExcelAST = right

    def __repr__(self) -> str:
        return f"BinOp({self.left!r}, {self.op!r}, {self.right!r})"


class UnaryOp(ExcelAST):
    def __init__(self, op: str, operand: ExcelAST) -> None:
        self.op: str = op
        self.operand: ExcelAST = operand

    def __repr__(self) -> str:
        return f"UnaryOp({self.op!r}, {self.operand!r})"
