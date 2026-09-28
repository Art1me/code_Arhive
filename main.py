from typing import Literal

from fastapi import FastAPI, Query

from database import fetch_all, init_db
from schemas import FileStructure, FileSummary, SearchItem, StatsResponse, SymbolItem

app = FastAPI(title="Code Archive API", version="1.0.0")


@app.on_event("startup")
def startup_event() -> None:
    init_db(clear=False)


@app.get("/api/files", response_model=list[FileSummary])
def list_files(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[FileSummary]:
    rows = fetch_all(
        """
        SELECT
            f.name,
            f.path,
            SUM(CASE WHEN s.type = 'function' THEN 1 ELSE 0 END) AS functions_count,
            SUM(CASE WHEN s.type = 'class' THEN 1 ELSE 0 END) AS classes_count,
            COUNT(s.id) AS symbols_count
        FROM files f
        LEFT JOIN symbols s ON s.file_id = f.id
        GROUP BY f.id
        ORDER BY f.name
        LIMIT ? OFFSET ?;
        """,
        (limit, offset),
    )

    return [
        FileSummary(
            name=row["name"],
            path=row["path"],
            functions_count=int(row["functions_count"] or 0),
            classes_count=int(row["classes_count"] or 0),
            symbols_count=int(row["symbols_count"] or 0),
        )
        for row in rows
    ]


@app.get("/api/files/{name}/structure", response_model=list[FileStructure] | list)
def file_structure(name: str) -> list[FileStructure] | list:
    file_rows = fetch_all(
        "SELECT id, name, path FROM files WHERE name = ? COLLATE NOCASE LIMIT 1;",
        (name,),
    )
    if not file_rows:
        return []

    file_row = file_rows[0]
    symbol_rows = fetch_all(
        """
        SELECT name, type, start_line, end_line, docstring
        FROM symbols
        WHERE file_id = ?
        ORDER BY start_line, name;
        """,
        (file_row["id"],),
    )

    symbols = [
        SymbolItem(
            name=row["name"],
            type=row["type"],
            start_line=int(row["start_line"]),
            end_line=int(row["end_line"]),
            docstring=row["docstring"],
        )
        for row in symbol_rows
    ]

    return [
        FileStructure(name=file_row["name"], path=file_row["path"], symbols=symbols)
    ]


@app.get("/api/search", response_model=list[SearchItem])
def search_symbols(
    q: str = Query(..., min_length=1),
    type: Literal["function", "class"] | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[SearchItem]:
    keyword = f"%{q.strip()}%"

    if type:
        rows = fetch_all(
            """
            SELECT
                f.name AS file,
                f.path AS path,
                s.name,
                s.type,
                s.start_line,
                s.end_line,
                s.docstring
            FROM symbols s
            JOIN files f ON f.id = s.file_id
            WHERE s.type = ?
              AND (
                s.name LIKE ? COLLATE NOCASE
                OR s.docstring LIKE ? COLLATE NOCASE
              )
            ORDER BY s.name, f.name
            LIMIT ? OFFSET ?;
            """,
            (type, keyword, keyword, limit, offset),
        )
    else:
        rows = fetch_all(
            """
            SELECT
                f.name AS file,
                f.path AS path,
                s.name,
                s.type,
                s.start_line,
                s.end_line,
                s.docstring
            FROM symbols s
            JOIN files f ON f.id = s.file_id
            WHERE s.name LIKE ? COLLATE NOCASE
               OR s.docstring LIKE ? COLLATE NOCASE
            ORDER BY s.name, f.name
            LIMIT ? OFFSET ?;
            """,
            (keyword, keyword, limit, offset),
        )

    return [
        SearchItem(
            file=row["file"],
            path=row["path"],
            name=row["name"],
            type=row["type"],
            start_line=int(row["start_line"]),
            end_line=int(row["end_line"]),
            docstring=row["docstring"],
        )
        for row in rows
    ]


@app.get("/api/stats", response_model=StatsResponse)
def get_stats() -> StatsResponse:
    stats_rows = fetch_all(
        """
        SELECT
            (SELECT COUNT(*) FROM files) AS files,
            (SELECT COUNT(*) FROM symbols WHERE type = 'function') AS functions,
            (SELECT COUNT(*) FROM symbols WHERE type = 'class') AS classes,
            (SELECT COUNT(*) FROM symbols) AS symbols;
        """
    )

    row = stats_rows[0]
    return StatsResponse(
        files=int(row["files"] or 0),
        functions=int(row["functions"] or 0),
        classes=int(row["classes"] or 0),
        symbols=int(row["symbols"] or 0),
    )
