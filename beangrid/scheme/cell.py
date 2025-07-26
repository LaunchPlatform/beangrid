from pydantic import BaseModel


class Cell(BaseModel):
    id: str
    value: str | None = None
    formula: str | None = None


class Sheet(BaseModel):
    name: str
    cells: list[Cell]

    def get_cell_dict(self) -> dict[str, Cell]:
        """Create a dictionary mapping cell ID to cell for easy lookup."""
        return {cell.id: cell for cell in self.cells}


class Workbook(BaseModel):
    sheets: list[Sheet]

    def get_sheet_by_name(self, sheet_name: str) -> Sheet | None:
        """Get a sheet by name."""
        return next((s for s in self.sheets if s.name == sheet_name), None)
