from typing import Any
from typing import List
from typing import Optional
from typing import Union

from lark import Lark
from lark import Transformer
from lark import v_args

excel_grammar = r"""
    ?start: expr

    ?expr: func_call
         | cell_range
         | cell
         | number
         | string
         | bool
         | expr binop expr   -> bin_expr
         | "-" expr          -> neg
         | "+" expr          -> pos
         | "(" expr ")"

    func_call: NAME "(" [args] ")"
    args: expr ("," expr)*

    cell_range: cell ":" cell
    cell: SHEET_REF? CELL_REF

    number: NUMBER
    string: STRING
    bool: TRUE | FALSE

    binop: "+" | "-" | "*" | "/" | "^" | "&" | "=" | "<>" | "<=" | ">=" | "<" | ">"

    SHEET_REF: /[A-Za-z_][A-Za-z0-9_]*!/
    CELL_REF: /\$?[A-Za-z]{1,3}\$?\d{1,7}/

    NAME: /[A-Za-z_][A-Za-z0-9_.]*/
    NUMBER: /\d+(\.\d+)?([eE][+-]?\d+)?/
    STRING: /"(?:[^"]|"")*"/

    TRUE: /TRUE/i
    FALSE: /FALSE/i

    %import common.WS
    %ignore WS
"""


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
            return f"Cell({self.sheet!r}, {self.ref!r})"
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


@v_args(inline=True)
class ExcelTransformer(Transformer):
    def number(self, n: str) -> Number:
        return Number(n)

    def string(self, s: str) -> String:
        return String(s)

    def bool(self, b: str) -> Bool:
        return Bool(b)

    def cell(self, *args: str) -> Cell:
        if len(args) == 2:
            sheet, ref = args
            return Cell(ref, sheet=sheet[:-1])  # remove trailing '!'
        else:
            (ref,) = args
            return Cell(ref)

    def cell_range(self, start: Cell, end: Cell) -> CellRange:
        return CellRange(start, end)

    def func_call(self, name: str, *args: ExcelAST) -> FuncCall:
        return FuncCall(str(name), list(args))

    def args(self, *args: ExcelAST) -> List[ExcelAST]:
        return list(args)

    def bin_expr(self, left: ExcelAST, op: str, right: ExcelAST) -> BinOp:
        return BinOp(left, str(op), right)

    def neg(self, expr: ExcelAST) -> UnaryOp:
        return UnaryOp("-", expr)

    def pos(self, expr: ExcelAST) -> UnaryOp:
        return UnaryOp("+", expr)

    def NAME(self, token: str) -> str:
        return str(token)

    def SHEET_REF(self, token: str) -> str:
        return str(token)

    def CELL_REF(self, token: str) -> str:
        return str(token)

    def NUMBER(self, token: str) -> str:
        return str(token)

    def STRING(self, token: str) -> str:
        return str(token)

    def TRUE(self, token: str) -> str:
        return str(token)

    def FALSE(self, token: str) -> str:
        return str(token)

    def binop(self, token: str) -> str:
        return str(token)


def get_excel_parser() -> Lark:
    parser = Lark(excel_grammar, parser="lalr", transformer=ExcelTransformer())
    return parser


def parse_excel_formula(formula: str) -> ExcelAST:
    parser = get_excel_parser()
    return parser.parse(formula)
