import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import database  # noqa: E402
from main import app  # noqa: E402


@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    db_file = tmp_path / "test_code_archive.db"
    monkeypatch.setattr(database, "DB_PATH", db_file)
    database.init_db(clear=True)
    yield db_file


@pytest.fixture
def populated_db(temp_db):
    from database import get_connection, insert_file, insert_symbol

    with get_connection() as conn:
        f1_id = insert_file(conn, "sample_code/auth_service.py", "auth_service.py")
        insert_symbol(conn, f1_id, "login", "function", 10, 22, "Authenticate user")
        insert_symbol(conn, f1_id, "logout", "function", 25, 30, "")
        insert_symbol(conn, f1_id, "AuthService", "class", 5, 40, "Service handling auth logic")

        f2_id = insert_file(conn, "sample_code/payment_service.py", "payment_service.py")
        insert_symbol(conn, f2_id, "PaymentProcessor", "class", 3, 60, "Processes payments")
        insert_symbol(conn, f2_id, "charge_user", "function", 15, 30, "Charge a user for service")

        conn.commit()
    return temp_db


@pytest.fixture
def client(populated_db):
    return TestClient(app)


@pytest.fixture
def sample_py_files(tmp_path):
    mod1 = tmp_path / "sample.py"
    mod1.write_text(
        '''
"""Sample module."""


class User:
    """User model."""

    def __init__(self, name: str) -> None:
        self.name = name


def greet(user: User) -> str:
    """Greet the user."""
    return f"Hello, {user.name}"
'''.strip(),
        encoding="utf-8",
    )

    broken = tmp_path / "broken.py"
    broken.write_text("def broken(:\n    pass", encoding="utf-8")

    return tmp_path
