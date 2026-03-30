"""Tests for helper functions in deploy scripts"""
from unittest.mock import MagicMock

from deploy.deploy_n8n_hetzner import run


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
    ssh = _mock_ssh(stdout="container running")
    result = run(ssh, "docker ps")
    assert result == "container running"


def test_run_with_label(capsys):
    ssh = _mock_ssh(stdout="ok")
    run(ssh, "echo ok", label="DEPLOY STEP")
    captured = capsys.readouterr()
    assert "DEPLOY STEP" in captured.out


def test_run_strips_whitespace():
    ssh = _mock_ssh(stdout="  data  \n")
    result = run(ssh, "cmd")
    assert result == "data"


def test_run_hides_warnings(capsys):
    """stderr containing WARNING should not be printed."""
    ssh = _mock_ssh(stdout="", stderr="WARNING: something")
    run(ssh, "cmd")
    captured = capsys.readouterr()
    assert "[stderr]" not in captured.out


def test_run_shows_real_errors(capsys):
    """stderr without WARNING should be printed."""
    ssh = _mock_ssh(stdout="", stderr="fatal error occurred")
    run(ssh, "cmd")
    captured = capsys.readouterr()
    assert "[stderr]" in captured.out
    assert "fatal error occurred" in captured.out


def test_run_custom_timeout():
    ssh = _mock_ssh(stdout="ok")
    run(ssh, "slow_cmd", timeout=300)
    ssh.exec_command.assert_called_once_with("slow_cmd", timeout=300)


def test_run_default_timeout():
    ssh = _mock_ssh(stdout="ok")
    run(ssh, "fast_cmd")
    ssh.exec_command.assert_called_once_with("fast_cmd", timeout=120)


def test_run_truncates_long_command(capsys):
    """Printed command should be truncated to 100 chars."""
    ssh = _mock_ssh(stdout="ok")
    long_cmd = "x" * 200
    run(ssh, long_cmd)
    captured = capsys.readouterr()
    assert "x" * 100 in captured.out
    assert "x" * 200 not in captured.out
