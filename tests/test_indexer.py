from pathlib import Path

from indexer import parse_python_file


def test_parse_python_file_find_all_symbols(sample_py_files: Path):
    file = sample_py_files / "sample.py"
    symbols = parse_python_file(file)

    names = {s["name"] for s in symbols}
    assert "User" in names
    assert "__init__" in names
    assert "greet" in names


def test_parse_python_file_symbol_types(sample_py_files: Path):
    file = sample_py_files / "sample.py"
    symbols = parse_python_file(file)

    classes = [s for s in symbols if s["type"] == "class"]
    funcs = [s for s in symbols if s["type"] == "function"]

    assert len(classes) == 1
    assert classes[0]["name"] == "User"
    assert {f["name"] for f in funcs} == {"__init__", "greet"}


def test_parse_python_file_docstrings(sample_py_files: Path):
    file = sample_py_files / "sample.py"
    symbols = {s["name"]: s for s in parse_python_file(file)}

    assert "User model." in symbols["User"]["docstring"]
    assert "Greet the user." in symbols["greet"]["docstring"]


def test_parse_python_file_line_numbers(sample_py_files: Path):
    file = sample_py_files / "sample.py"
    symbols = {s["name"]: s for s in parse_python_file(file)}

    greet = symbols["greet"]
    assert greet["start_line"] < greet["end_line"]
    assert greet["start_line"] > 0


def test_parse_python_file_syntax_error_returns_empty(sample_py_files: Path):
    file = sample_py_files / "broken.py"
    symbols = parse_python_file(file)
    assert symbols == []


def test_parse_python_file_missing_returns_empty(tmp_path: Path):
    symbols = parse_python_file(tmp_path / "not_exists.py")
    assert symbols == []
