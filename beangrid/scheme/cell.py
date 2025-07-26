from pydantic import BaseModel


class Cell(BaseModel):
    id: str
    value: str | None
    formula: str | None


class Sheet(BaseModel):
    name: str
    cells: list[Cell]
    
    def get_cell_dict(self) -> dict[str, Cell]:
        """Create a dictionary mapping cell ID to cell for easy lookup."""
        return {cell.id: cell for cell in self.cells}


class Workbook(BaseModel):
    sheets: list[Sheet]
