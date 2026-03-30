"""Verify all Python scripts in the repo parse without syntax errors."""
import ast
import os

import pytest

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..")


def _collect_py_files():
    """Collect all .py files under scripts/."""
    py_files = []
    for root, _dirs, files in os.walk(SCRIPTS_DIR):
        if "__pycache__" in root:
            continue
        for f in files:
            if f.endswith(".py"):
                py_files.append(os.path.join(root, f))
    return sorted(py_files)


@pytest.mark.parametrize("filepath", _collect_py_files(), ids=lambda p: os.path.relpath(p, SCRIPTS_DIR))
def test_python_file_parses(filepath):
    """Each Python file must be valid syntax."""
    with open(filepath, "r", encoding="utf-8") as fh:
        source = fh.read()
    ast.parse(source, filename=filepath)
