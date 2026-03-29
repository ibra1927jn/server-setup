"""Tests for diagnostics/check_server.py run() helper"""
from unittest.mock import MagicMock
from diagnostics.check_server import run


def _mock_ssh(stdout="", stderr=""):
    """Create a mock SSH client that returns given stdout/stderr."""
    ssh = MagicMock()
    o = MagicMock()
    o.read.return_value = stdout.encode()
    e = MagicMock()
    e.read.return_value = stderr.encode()
    ssh.exec_command.return_value = (MagicMock(), o, e)
    return ssh


def test_run_returns_stdout():
    ssh = _mock_ssh(stdout="Linux 6.1.0")
    result = run(ssh, "uname -r")
    assert result == "Linux 6.1.0"
    ssh.exec_command.assert_called_once_with("uname -r", timeout=120)


def test_run_with_label(capsys):
    ssh = _mock_ssh(stdout="ok")
    run(ssh, "echo ok", label="TEST")
    captured = capsys.readouterr()
    assert "=== TEST ===" in captured.out


def test_run_strips_whitespace():
    ssh = _mock_ssh(stdout="  hello  \n")
    result = run(ssh, "echo hello")
    assert result == "hello"


def test_run_empty_output():
    ssh = _mock_ssh(stdout="", stderr="")
    result = run(ssh, "true")
    assert result == ""


def test_run_stderr_shown(capsys):
    ssh = _mock_ssh(stdout="", stderr="warning: something")
    run(ssh, "cmd")
    captured = capsys.readouterr()
    assert "[stderr]" in captured.out
    assert "warning: something" in captured.out
