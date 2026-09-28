import sqlite3

import pytest

from database import (
    fetch_all,
    get_connection,
    init_db,
    insert_file,
    insert_symbol,
)


def test_init_db_creates_tables(temp_db):
    with get_connection() as conn:
        tables = [
            r["name"]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table';"
            ).fetchall()
        ]

    assert "files" in tables
    assert "symbols" in tables


def test_init_db_creates_indexes(temp_db):
    with get_connection() as conn:
        indexes = [
            r["name"]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index';"
            ).fetchall()
        ]

    assert any("idx_symbols_name" in i for i in indexes)
    assert any("idx_symbols_type" in i for i in indexes)
    assert any("idx_files_name" in i for i in indexes)


def test_init_db_clear_flag(temp_db):
    with get_connection() as conn:
        fid = insert_file(conn, "x/y.py", "y.py")
        insert_symbol(conn, fid, "foo", "function", 1, 2, "")
        conn.commit()

    init_db(clear=True)
    rows = fetch_all("SELECT COUNT(*) AS c FROM files;")
    assert rows[0]["c"] == 0


def test_insert_file_returns_id(temp_db):
    with get_connection() as conn:
        fid = insert_file(conn, "mod/a.py", "a.py")

    assert isinstance(fid, int)
    assert fid > 0


def test_insert_file_unique_path(temp_db):
    with get_connection() as conn:
        insert_file(conn, "mod/a.py", "a.py")
        with pytest.raises(sqlite3.IntegrityError):
            insert_file(conn, "mod/a.py", "a.py")


def test_insert_symbol_valid(temp_db):
    with get_connection() as conn:
        fid = insert_file(conn, "mod/a.py", "a.py")
        insert_symbol(conn, fid, "my_func", "function", 1, 5, "docs")
        conn.commit()

    rows = fetch_all("SELECT name, type, docstring FROM symbols;")
    assert len(rows) == 1
    assert rows[0]["name"] == "my_func"
    assert rows[0]["type"] == "function"
    assert rows[0]["docstring"] == "docs"


def test_insert_symbol_invalid_type_rejected(temp_db):
    with get_connection() as conn:
        fid = insert_file(conn, "mod/a.py", "a.py")
        with pytest.raises(sqlite3.IntegrityError):
            insert_symbol(conn, fid, "x", "method", 1, 2, "")


def test_fetch_all_empty_result(temp_db):
    rows = fetch_all("SELECT * FROM files WHERE name = 'zzz';")
    assert rows == []
