"""Tests for check_server.py run() function and main() orchestration."""

from unittest.mock import patch

from conftest import mock_ssh as _mock_ssh


def test_run_returns_stdout():
    from diagnostics.check_server import run

    ssh = _mock_ssh(stdout="uptime: 5 days")
    result = run(ssh, "uptime", "UPTIME")
    assert result == "uptime: 5 days"


def test_run_calls_exec_command():
    from diagnostics.check_server import run

    ssh = _mock_ssh()
    run(ssh, "df -h /", "DISK")
    ssh.exec_command.assert_called_once_with("df -h /", timeout=120)


def test_run_prints_label(capsys):
    from diagnostics.check_server import run

    ssh = _mock_ssh(stdout="ok")
    run(ssh, "test", "MY LABEL")
    captured = capsys.readouterr()
    assert "MY LABEL" in captured.out


def test_run_no_label(capsys):
    from diagnostics.check_server import run

    ssh = _mock_ssh(stdout="ok")
    run(ssh, "test")
    captured = capsys.readouterr()
    assert "===" not in captured.out


def test_run_prints_stderr(capsys):
    from diagnostics.check_server import run

    ssh = _mock_ssh(stdout="", stderr="some error")
    run(ssh, "test")
    captured = capsys.readouterr()
    assert "some error" in captured.out


def test_run_empty_stderr_not_printed(capsys):
    from diagnostics.check_server import run

    ssh = _mock_ssh(stdout="ok", stderr="")
    run(ssh, "test")
    captured = capsys.readouterr()
    assert "[stderr]" not in captured.out


def test_run_truncates_long_command(capsys):
    from diagnostics.check_server import run

    ssh = _mock_ssh(stdout="ok")
    long_cmd = "x" * 200
    run(ssh, long_cmd)
    captured = capsys.readouterr()
    # Should only print first 80 chars of command
    assert "x" * 80 in captured.out
    assert "x" * 200 not in captured.out


@patch("diagnostics.check_server.get_ssh_client")
@patch("diagnostics.check_server.VPS_HOST", "10.0.0.1")
def test_main_runs_all_checks(mock_get_ssh):
    from diagnostics.check_server import main

    ssh = _mock_ssh(stdout="ok")
    mock_get_ssh.return_value = ssh
    main()
    cmds = [c[0][0] for c in ssh.exec_command.call_args_list]
    assert any("df" in c for c in cmds)
    assert any("free" in c for c in cmds)
    assert any("docker" in c for c in cmds)
    assert any("nginx" in c for c in cmds)


@patch("diagnostics.check_server.get_ssh_client")
@patch("diagnostics.check_server.VPS_HOST", "10.0.0.1")
def test_main_closes_ssh(mock_get_ssh):
    from diagnostics.check_server import main

    ssh = _mock_ssh(stdout="ok")
    mock_get_ssh.return_value = ssh
    main()
    ssh.close.assert_called_once()
