"""Verify all Python scripts in the repo parse without syntax errors."""

import ast
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).parent.parent


def _collect_py_files():
    """Collect all .py files under scripts/."""
    py_files = []
    for root, _dirs, files in SCRIPTS_DIR.walk():
        if "__pycache__" in str(root):
            continue
        py_files.extend(str(root / f) for f in files if f.endswith(".py"))
    return sorted(py_files)


@pytest.mark.parametrize("filepath", _collect_py_files(), ids=lambda p: str(Path(p).relative_to(SCRIPTS_DIR)))
def test_python_file_parses(filepath):
    """Each Python file must be valid syntax."""
    source = Path(filepath).read_text(encoding="utf-8")
    ast.parse(source, filename=filepath)
