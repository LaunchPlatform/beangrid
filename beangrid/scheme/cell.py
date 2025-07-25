from pydantic import BaseModel



class Cell(BaseModel):
    id: str
    value: str | None
    formula: str | None
