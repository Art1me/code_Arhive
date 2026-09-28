import ast
import sys
from pathlib import Path

from database import get_connection, init_db, insert_file, insert_symbol


def parse_python_file(file_path: Path) -> list[dict[str, object]]:
    try:
        source = file_path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"[WARN] Cannot read file {file_path}: {exc}")
        return []

    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        print(f"[WARN] Syntax error in {file_path}: {exc}")
        return []

    symbols: list[dict[str, object]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            symbols.append(
                {
                    "name": node.name,
                    "type": "function",
                    "start_line": int(node.lineno),
                    "end_line": int(node.end_lineno or node.lineno),
                    "docstring": ast.get_docstring(node) or "",
                }
            )
        elif isinstance(node, ast.ClassDef):
            symbols.append(
                {
                    "name": node.name,
                    "type": "class",
                    "start_line": int(node.lineno),
                    "end_line": int(node.end_lineno or node.lineno),
                    "docstring": ast.get_docstring(node) or "",
                }
            )

    return symbols


def index_directory(target_dir: Path) -> None:
    init_db(clear=True)

    py_files = sorted(target_dir.rglob("*.py"))

    with get_connection() as conn:
        conn.execute("PRAGMA foreign_keys = ON;")

        for file_path in py_files:
            relative_path = file_path.relative_to(Path.cwd()).as_posix()
            file_id = insert_file(conn, relative_path, file_path.name)

            symbols = parse_python_file(file_path)
            for symbol in symbols:
                insert_symbol(
                    conn,
                    file_id,
                    symbol["name"],
                    symbol["type"],
                    symbol["start_line"],
                    symbol["end_line"],
                    symbol["docstring"],
                )

        conn.commit()

    print(f"Indexed {len(py_files)} files from: {target_dir}")


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python indexer.py <directory>")
        sys.exit(1)

    target_dir = Path(sys.argv[1]).resolve()
    if not target_dir.exists() or not target_dir.is_dir():
        print(f"Directory does not exist: {target_dir}")
        sys.exit(1)

    index_directory(target_dir)


if __name__ == "__main__":
    main()
