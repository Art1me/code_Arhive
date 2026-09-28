from typing import Literal

from pydantic import BaseModel


class FileSummary(BaseModel):
    name: str
    path: str
    functions_count: int
    classes_count: int
    symbols_count: int


class SymbolItem(BaseModel):
    name: str
    type: Literal["function", "class"]
    start_line: int
    end_line: int
    docstring: str


class FileStructure(BaseModel):
    name: str
    path: str
    symbols: list[SymbolItem]


class SearchItem(BaseModel):
    file: str
    path: str
    name: str
    type: Literal["function", "class"]
    start_line: int
    end_line: int
    docstring: str


class StatsResponse(BaseModel):
    files: int
    functions: int
    classes: int
    symbols: int
