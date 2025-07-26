from pydantic import BaseModel


class Cell(BaseModel):
    id: str
    value: str | None
    formula: str | None


class Sheet(BaseModel):
    name: str
    cells: list[Cell]


class Workbook(BaseModel):
    sheets: list[Sheet]
