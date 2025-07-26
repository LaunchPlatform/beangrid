from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import Dict
from typing import List
from typing import Set
from typing import Tuple
from .evaluator import DependencyGraph
from .evaluator import FormulaEvaluator
from .parser import parse_excel_formula
from beangrid.scheme.cell import Cell as SchemeCell
from beangrid.scheme.cell import Sheet
from beangrid.scheme.cell import Workbook


class Processor(ABC):
    """
    Abstract base class for spreadsheet processors.
    Defines the interface for calculating cell values based on formulas.
    """

    @abstractmethod
    def process_workbook(self, workbook: Workbook) -> Workbook:
        """
        Process the entire workbook, calculating all cell values.
        Returns a new Workbook with calculated values.
        """
        pass

    @abstractmethod
    def process_sheet(self, sheet: Sheet, workbook: Workbook) -> Sheet:
        """
        Process a single sheet, calculating all cell values.
        Returns a new Sheet with calculated values.
        """
        pass

    @abstractmethod
    def process_cell(
        self, cell: SchemeCell, sheet: Sheet, workbook: Workbook
    ) -> SchemeCell:
        """
        Process a single cell, calculating its value if it contains a formula.
        Returns a new Cell with the calculated value.
        """
        pass


class FormulaProcessor(Processor):
    """
    A processor that evaluates formulas in cells with dependency tracking.
    """

    def __init__(self):
        self.dependency_graph = DependencyGraph()
        self.evaluated_cells: Dict[str, Any] = {}

    def process_workbook(self, workbook: Workbook) -> Workbook:
        # First pass: build dependency graph
        self._build_dependency_graph(workbook)

        # Check for circular dependencies
        cycles = self.dependency_graph.detect_cycles()
        if cycles:
            raise ValueError(f"Circular dependencies detected: {cycles}")

        # Get evaluation order
        evaluation_order = self.dependency_graph.get_evaluation_order()

        # Second pass: evaluate cells in dependency order
        evaluator = FormulaEvaluator(workbook)

        for cell_id in evaluation_order:
            self._evaluate_cell_with_dependencies(cell_id, workbook, evaluator)

        # Third pass: create new workbook with computed values
        new_sheets = [self.process_sheet(sheet, workbook) for sheet in workbook.sheets]
        return Workbook(sheets=new_sheets)

    def process_sheet(self, sheet: Sheet, workbook: Workbook) -> Sheet:
        new_cells = [self.process_cell(cell, sheet, workbook) for cell in sheet.cells]
        return Sheet(name=sheet.name, cells=new_cells)

    def process_cell(
        self, cell: SchemeCell, sheet: Sheet, workbook: Workbook
    ) -> SchemeCell:
        if cell.formula:
            # Use the pre-computed value from the evaluation phase
            value = self.evaluated_cells.get(
                f"{sheet.name}!{cell.id}" if sheet.name else cell.id
            )
            if value is None:
                value = f"#ERROR: Could not evaluate formula"
        else:
            value = cell.value

        # Format values appropriately
        if value is None:
            formatted_value = None
        elif isinstance(value, bool):
            formatted_value = str(value)
        elif isinstance(value, (int, float)):
            formatted_value = f"{float(value):.1f}"
        else:
            formatted_value = str(value)

        return SchemeCell(
            id=cell.id,
            value=formatted_value,
            formula=cell.formula,
        )

    def _build_dependency_graph(self, workbook: Workbook):
        """Build dependency graph by analyzing all formulas."""
        for sheet in workbook.sheets:
            for cell in sheet.cells:
                if cell.formula:
                    self._extract_dependencies(cell, sheet, workbook)

    def _extract_dependencies(self, cell: SchemeCell, sheet: Sheet, workbook: Workbook):
        """Extract cell dependencies from a formula."""
        try:
            ast = parse_excel_formula(cell.formula)
            cell_id = f"{sheet.name}!{cell.id}" if sheet.name else cell.id
            dependencies = self._find_cell_dependencies(ast, sheet.name)

            for dep in dependencies:
                self.dependency_graph.add_dependency(cell_id, dep)
            
            # Ensure the cell is added to the dependency graph even if it has no dependencies
            if cell_id not in self.dependency_graph.dependencies:
                self.dependency_graph.dependencies[cell_id] = set()
        except Exception:
            # If parsing fails, skip this cell
            pass

    def _find_cell_dependencies(self, ast, current_sheet: str = "") -> Set[str]:
        """Recursively find all cell dependencies in an AST."""
        dependencies = set()

        if hasattr(ast, "ref"):  # Cell reference
            cell_ref = ast.ref
            if ast.sheet:
                cell_ref = f"{ast.sheet}!{cell_ref}"
            elif current_sheet:
                cell_ref = f"{current_sheet}!{cell_ref}"
            dependencies.add(cell_ref)

        elif hasattr(ast, "start") and hasattr(ast, "end"):  # Cell range
            start_ref = ast.start.ref
            end_ref = ast.end.ref

            if ast.start.sheet:
                start_ref = f"{ast.start.sheet}!{start_ref}"
            elif current_sheet:
                start_ref = f"{current_sheet}!{start_ref}"

            if ast.end.sheet:
                end_ref = f"{ast.end.sheet}!{end_ref}"
            elif current_sheet:
                end_ref = f"{current_sheet}!{end_ref}"

            dependencies.add(start_ref)
            dependencies.add(end_ref)

        elif hasattr(ast, "left") and hasattr(ast, "right"):  # Binary operation
            dependencies.update(self._find_cell_dependencies(ast.left, current_sheet))
            dependencies.update(self._find_cell_dependencies(ast.right, current_sheet))

        elif hasattr(ast, "operand"):  # Unary operation
            dependencies.update(
                self._find_cell_dependencies(ast.operand, current_sheet)
            )

        elif hasattr(ast, "args"):  # Function call
            for arg in ast.args:
                dependencies.update(self._find_cell_dependencies(arg, current_sheet))

        return dependencies

    def _evaluate_cell_with_dependencies(
        self, cell_id: str, workbook: Workbook, evaluator: FormulaEvaluator
    ):
        """Evaluate a cell and store its result."""
        # Find the cell in the workbook
        cell = None
        sheet_name = ""

        for sheet in workbook.sheets:
            for c in sheet.cells:
                current_cell_id = f"{sheet.name}!{c.id}" if sheet.name else c.id
                if current_cell_id == cell_id:
                    cell = c
                    sheet_name = sheet.name
                    break
            if cell:
                break

        if not cell or not cell.formula:
            return

        # Create a custom resolver that uses our computed values
        class ComputedCellResolver:
            def __init__(self, workbook, computed_values):
                self.workbook = workbook
                self.computed_values = computed_values
                self._cell_cache = {}

                # Build cell cache
                for sheet in workbook.sheets:
                    for cell in sheet.cells:
                        key = f"{sheet.name}!{cell.id}" if sheet.name else cell.id
                        self._cell_cache[key] = cell

            def get_cell_value(self, cell_ref: str, current_sheet: str = "") -> Any:
                # Handle sheet references like "Sheet1!A1"
                if "!" in cell_ref:
                    sheet_name, cell_id = cell_ref.split("!", 1)
                    key = f"{sheet_name}!{cell_id}"
                else:
                    # Use current sheet if no sheet specified
                    key = f"{current_sheet}!{cell_ref}" if current_sheet else cell_ref

                # First check if we have a computed value
                if key in self.computed_values:
                    return self.computed_values[key]

                cell = self._cell_cache.get(key)
                if cell is None:
                    return None

                # If cell has a formula, check if we have a computed value
                if cell.formula:
                    # Check if we have a computed value for this cell
                    cell_key = f"{sheet_name}!{cell.id}" if sheet_name else cell.id
                    if cell_key in self.computed_values:
                        return self.computed_values[cell_key]
                    # If no computed value yet, return None to avoid circular dependencies
                    return None

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
                import re
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

        # Create evaluator with custom resolver
        evaluator.resolver = ComputedCellResolver(workbook, self.evaluated_cells)

        # Evaluate the formula
        try:
            result = evaluator.evaluate(cell.formula, sheet_name)
            self.evaluated_cells[cell_id] = result
        except Exception as e:
            self.evaluated_cells[cell_id] = f"#ERROR: {str(e)}"
