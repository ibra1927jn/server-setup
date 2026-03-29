"""Tests for diagnostics/check_server.py run() helper and main()"""
from unittest.mock import MagicMock, patch
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


@patch("diagnostics.check_server.get_ssh_client")
def test_main_calls_six_checks(mock_get_ssh):
    """main() should run 6 diagnostic commands and close the connection."""
    from diagnostics.check_server import main

    ssh = _mock_ssh(stdout="ok")
    mock_get_ssh.return_value = ssh
    main()
    assert ssh.exec_command.call_count == 6
    ssh.close.assert_called_once()


@patch("diagnostics.check_server.get_ssh_client")
def test_main_prints_done(mock_get_ssh, capsys):
    """main() should print DONE at the end."""
    from diagnostics.check_server import main

    mock_get_ssh.return_value = _mock_ssh(stdout="ok")
    main()
    captured = capsys.readouterr()
    assert "DONE" in captured.out
