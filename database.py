import sqlite3
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).resolve().parent / "code_archive.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(clear: bool = False) -> None:
    with get_connection() as conn:
        conn.execute("PRAGMA foreign_keys = ON;")

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS symbols (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                type TEXT NOT NULL CHECK(type IN ('function', 'class')),
                start_line INTEGER NOT NULL,
                end_line INTEGER NOT NULL,
                docstring TEXT NOT NULL DEFAULT '',
                FOREIGN KEY(file_id) REFERENCES files(id)
            );
            """
        )

        conn.execute("CREATE INDEX IF NOT EXISTS idx_symbols_name ON symbols(name COLLATE NOCASE);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_symbols_type ON symbols(type);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_files_name ON files(name COLLATE NOCASE);")

        if clear:
            conn.execute("DELETE FROM symbols;")
            conn.execute("DELETE FROM files;")
            conn.execute("DELETE FROM sqlite_sequence WHERE name IN ('files', 'symbols');")

        conn.commit()


def insert_file(conn: sqlite3.Connection, path: str, name: str) -> int:
    cursor = conn.execute(
        "INSERT INTO files (path, name) VALUES (?, ?);",
        (path, name),
    )
    return int(cursor.lastrowid)


def insert_symbol(
    conn: sqlite3.Connection,
    file_id: int,
    name: str,
    symbol_type: str,
    start_line: int,
    end_line: int,
    docstring: str,
) -> None:
    conn.execute(
        """
        INSERT INTO symbols (file_id, name, type, start_line, end_line, docstring)
        VALUES (?, ?, ?, ?, ?, ?);
        """,
        (file_id, name, symbol_type, start_line, end_line, docstring),
    )


def fetch_all(query: str, params: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
    return rows
