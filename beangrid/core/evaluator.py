import re
from collections import defaultdict
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Set
from typing import Tuple

from ..scheme.cell import Cell as SchemeCell
from ..scheme.cell import Sheet
from ..scheme.cell import Workbook
from .ast import BinOp
from .ast import Bool
from .ast import Cell
from .ast import CellRange
from .ast import ExcelAST
from .ast import FuncCall
from .ast import Number
from .ast import String
from .ast import UnaryOp
from .parser import parse_excel_formula


class CellResolver:
    """Resolves cell references to their values in a workbook."""

    def __init__(self, workbook: Workbook):
        self.workbook = workbook
        self._cell_cache: Dict[str, Any] = {}
        self._sheet_cache: Dict[str, Sheet] = {}

        # Build sheet cache
        for sheet in workbook.sheets:
            self._sheet_cache[sheet.name] = sheet

        # Build cell cache for quick lookup
        for sheet in workbook.sheets:
            for cell in sheet.cells:
                key = f"{sheet.name}!{cell.id}" if sheet.name else cell.id
                self._cell_cache[key] = cell

    def get_cell_value(self, cell_ref: str, current_sheet: str = "") -> Any:
        """Get the value of a cell reference."""
        # Handle sheet references like "Sheet1!A1"
        if "!" in cell_ref:
            sheet_name, cell_id = cell_ref.split("!", 1)
            key = f"{sheet_name}!{cell_id}"
        else:
            # Use current sheet if no sheet specified
            key = f"{current_sheet}!{cell_ref}" if current_sheet else cell_ref

        cell = self._cell_cache.get(key)
        if cell is None:
            return None

        # If cell has a formula, we need to evaluate it
        if cell.formula:
            # For now, return the formula string to avoid circular dependencies
            # In a full implementation, this would trigger formula evaluation
            return f"={cell.formula}"

        # Convert string values to appropriate types
        if cell.value is None:
            return None

        # Try to convert to number if possible
        try:
            if "." in cell.value:
                return float(cell.value)
            else:
                return int(cell.value)
        except ValueError:
            # If not a number, return as string
            return cell.value

    def get_cell_range_values(
        self, start_cell: str, end_cell: str, current_sheet: str = ""
    ) -> List[Any]:
        """Get values from a cell range."""
        # Parse cell references to get row/column numbers
        start_col, start_row = self._parse_cell_ref(start_cell)
        end_col, end_row = self._parse_cell_ref(end_cell)

        values = []
        for row in range(start_row, end_row + 1):
            for col in range(start_col, end_col + 1):
                cell_ref = self._format_cell_ref(col, row)
                value = self.get_cell_value(cell_ref, current_sheet)
                values.append(value)

        return values

    def _parse_cell_ref(self, cell_ref: str) -> Tuple[int, int]:
        """Parse cell reference like 'A1' to (column, row)."""
        match = re.match(r"([A-Z]+)(\d+)", cell_ref)
        if not match:
            raise ValueError(f"Invalid cell reference: {cell_ref}")

        col_str, row_str = match.groups()
        col = self._column_to_number(col_str)
        row = int(row_str)

        return col, row

    def _format_cell_ref(self, col: int, row: int) -> str:
        """Format column and row numbers to cell reference like 'A1'."""
        col_str = self._number_to_column(col)
        return f"{col_str}{row}"

    def _column_to_number(self, col_str: str) -> int:
        """Convert column string like 'A' to number."""
        result = 0
        for char in col_str:
            result = result * 26 + (ord(char.upper()) - ord("A") + 1)
        return result

    def _number_to_column(self, col_num: int) -> str:
        """Convert column number to string like 'A'."""
        result = ""
        while col_num > 0:
            col_num -= 1
            result = chr(ord("A") + (col_num % 26)) + result
            col_num //= 26
        return result


class FormulaEvaluator:
    """Evaluates Excel formulas by traversing the AST."""

    def __init__(self, workbook: Workbook):
        self.workbook = workbook
        self.resolver = CellResolver(workbook)
        self.current_sheet = ""

    def evaluate(self, formula: str, current_sheet: str = "") -> Any:
        """Evaluate an Excel formula."""
        try:
            ast = parse_excel_formula(formula)
            self.current_sheet = current_sheet
            return self._evaluate_ast(ast)
        except Exception as e:
            return f"#ERROR: {str(e)}"

    def _evaluate_ast(self, ast: ExcelAST) -> Any:
        """Recursively evaluate an AST node."""
        if isinstance(ast, Number):
            return ast.value
        elif isinstance(ast, String):
            return ast.value
        elif isinstance(ast, Bool):
            return ast.value
        elif isinstance(ast, Cell):
            return self._evaluate_cell(ast)
        elif isinstance(ast, CellRange):
            return self._evaluate_cell_range(ast)
        elif isinstance(ast, FuncCall):
            return self._evaluate_function(ast)
        elif isinstance(ast, BinOp):
            return self._evaluate_binary_op(ast)
        elif isinstance(ast, UnaryOp):
            return self._evaluate_unary_op(ast)
        else:
            raise ValueError(f"Unknown AST node type: {type(ast)}")

    def _evaluate_cell(self, cell: Cell) -> Any:
        """Evaluate a cell reference."""
        cell_ref = cell.ref
        if cell.sheet:
            cell_ref = f"{cell.sheet}!{cell_ref}"

        return self.resolver.get_cell_value(cell_ref, self.current_sheet)

    def _evaluate_cell_range(self, cell_range: CellRange) -> List[Any]:
        """Evaluate a cell range."""
        start_ref = cell_range.start.ref
        end_ref = cell_range.end.ref

        if cell_range.start.sheet:
            start_ref = f"{cell_range.start.sheet}!{start_ref}"
        if cell_range.end.sheet:
            end_ref = f"{cell_range.end.sheet}!{end_ref}"

        return self.resolver.get_cell_range_values(
            start_ref, end_ref, self.current_sheet
        )

    def _evaluate_function(self, func_call: FuncCall) -> Any:
        """Evaluate a function call."""
        func_name = func_call.name.upper()
        # Filter out None arguments (from empty function calls)
        args = [self._evaluate_ast(arg) for arg in func_call.args if arg is not None]

        if func_name == "SUM":
            return self._sum(args)
        elif func_name == "AVERAGE":
            return self._average(args)
        elif func_name == "COUNT":
            return self._count(args)
        elif func_name == "MAX":
            return self._max(args)
        elif func_name == "MIN":
            return self._min(args)
        elif func_name == "IF":
            return self._if(args)
        else:
            return "#NAME?"

    def _evaluate_binary_op(self, bin_op: BinOp) -> Any:
        """Evaluate a binary operation."""
        left = self._evaluate_ast(bin_op.left)
        right = self._evaluate_ast(bin_op.right)

        # Handle numeric operations
        if bin_op.op in ["+", "-", "*", "/", "^"]:
            if not isinstance(left, (int, float)) or not isinstance(
                right, (int, float)
            ):
                return "#VALUE!"

            if bin_op.op == "+":
                return left + right
            elif bin_op.op == "-":
                return left - right
            elif bin_op.op == "*":
                return left * right
            elif bin_op.op == "/":
                if right == 0:
                    return "#DIV/0!"
                return left / right
            elif bin_op.op == "^":
                return left**right

        # Handle comparison operations
        elif bin_op.op in ["=", "<>", "<=", ">=", "<", ">"]:
            if bin_op.op == "=":
                return left == right
            elif bin_op.op == "<>":
                return left != right
            elif bin_op.op == "<=":
                return left <= right
            elif bin_op.op == ">=":
                return left >= right
            elif bin_op.op == "<":
                return left < right
            elif bin_op.op == ">":
                return left > right

        # Handle string concatenation
        elif bin_op.op == "&":
            return str(left) + str(right)

        return "#VALUE!"

    def _evaluate_unary_op(self, unary_op: UnaryOp) -> Any:
        """Evaluate a unary operation."""
        operand = self._evaluate_ast(unary_op.operand)

        if not isinstance(operand, (int, float)):
            return "#VALUE!"

        if unary_op.op == "-":
            return -operand
        elif unary_op.op == "+":
            return operand

        return "#VALUE!"

    # Built-in function implementations
    def _sum(self, args: List[Any]) -> float:
        """SUM function implementation."""
        total = 0.0
        for arg in args:
            if isinstance(arg, list):
                total += self._sum(arg)
            elif isinstance(arg, (int, float)):
                total += arg
        return total

    def _average(self, args: List[Any]) -> float:
        """AVERAGE function implementation."""
        values = []
        for arg in args:
            if isinstance(arg, list):
                values.extend([v for v in arg if isinstance(v, (int, float))])
            elif isinstance(arg, (int, float)):
                values.append(arg)

        if not values:
            return 0.0
        return sum(values) / len(values)

    def _count(self, args: List[Any]) -> int:
        """COUNT function implementation."""
        count = 0
        for arg in args:
            if isinstance(arg, list):
                count += len([v for v in arg if v is not None])
            elif arg is not None:
                count += 1
        return count

    def _max(self, args: List[Any]) -> Any:
        """MAX function implementation."""
        values = []
        for arg in args:
            if isinstance(arg, list):
                values.extend([v for v in arg if isinstance(v, (int, float))])
            elif isinstance(arg, (int, float)):
                values.append(arg)

        return max(values) if values else 0

    def _min(self, args: List[Any]) -> Any:
        """MIN function implementation."""
        values = []
        for arg in args:
            if isinstance(arg, list):
                values.extend([v for v in arg if isinstance(v, (int, float))])
            elif isinstance(arg, (int, float)):
                values.append(arg)

        return min(values) if values else 0

    def _if(self, args: List[Any]) -> Any:
        """IF function implementation."""
        if len(args) < 2:
            return "#VALUE!"

        condition = args[0]
        true_value = args[1]
        false_value = args[2] if len(args) > 2 else False

        if condition:
            return true_value
        else:
            return false_value


class DependencyGraph:
    """Builds and manages dependency graphs for formula evaluation."""

    def __init__(self):
        self.dependencies: Dict[str, Set[str]] = defaultdict(set)
        self.reverse_dependencies: Dict[str, Set[str]] = defaultdict(set)

    def add_dependency(self, cell_id: str, depends_on: str):
        """Add a dependency relationship."""
        self.dependencies[cell_id].add(depends_on)
        self.reverse_dependencies[depends_on].add(cell_id)

    def get_dependencies(self, cell_id: str) -> Set[str]:
        """Get all dependencies for a cell."""
        return self.dependencies.get(cell_id, set())

    def get_dependents(self, cell_id: str) -> Set[str]:
        """Get all cells that depend on this cell."""
        return self.reverse_dependencies.get(cell_id, set())

    def detect_cycles(self) -> List[List[str]]:
        """Detect circular dependencies."""
        visited = set()
        rec_stack = set()
        cycles = []

        def dfs(cell_id: str, path: List[str]):
            visited.add(cell_id)
            rec_stack.add(cell_id)
            path.append(cell_id)

            for dep in self.dependencies.get(cell_id, set()):
                if dep not in visited:
                    dfs(dep, path.copy())
                elif dep in rec_stack:
                    # Found a cycle
                    cycle_start = path.index(dep)
                    cycles.append(path[cycle_start:] + [dep])

            rec_stack.remove(cell_id)

        for cell_id in self.dependencies:
            if cell_id not in visited:
                dfs(cell_id, [])

        return cycles

    def get_evaluation_order(self) -> List[str]:
        """Get cells in dependency order for evaluation."""
        # Simple topological sort
        in_degree = defaultdict(int)
        
        # Initialize in_degree for all cells that have dependencies
        for cell_id, deps in self.dependencies.items():
            for dep in deps:
                in_degree[cell_id] += 1
                # Also initialize in_degree for dependencies that might not be in self.dependencies
                if dep not in in_degree:
                    in_degree[dep] = 0

        # Add all cells from dependencies to in_degree if they're not already there
        for cell_id in self.dependencies:
            if cell_id not in in_degree:
                in_degree[cell_id] = 0

        queue = [cell_id for cell_id in in_degree if in_degree[cell_id] == 0]
        result = []

        while queue:
            cell_id = queue.pop(0)
            result.append(cell_id)

            for dependent in self.reverse_dependencies.get(cell_id, set()):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        return result
