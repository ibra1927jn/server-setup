"""Tests for execute_daily_briefing.py find_workflow_id function"""

import json
from unittest.mock import MagicMock, patch

from execute_daily_briefing import find_workflow_id, main


def test_find_existing_workflow():
    workflows = [
        {"name": "Daily Briefing", "id": "abc123"},
        {"name": "Uptime Monitor", "id": "def456"},
    ]
    assert find_workflow_id(workflows, "Daily Briefing") == "abc123"


def test_find_second_workflow():
    workflows = [
        {"name": "Daily Briefing", "id": "abc123"},
        {"name": "Uptime Monitor", "id": "def456"},
    ]
    assert find_workflow_id(workflows, "Uptime Monitor") == "def456"


def test_workflow_not_found():
    workflows = [
        {"name": "Daily Briefing", "id": "abc123"},
    ]
    assert find_workflow_id(workflows, "Nonexistent") is None


def test_empty_list():
    assert find_workflow_id([], "Daily Briefing") is None


def test_workflow_missing_name():
    workflows = [{"id": "abc123"}]
    assert find_workflow_id(workflows, "Daily Briefing") is None


def test_workflow_missing_id():
    workflows = [{"name": "Daily Briefing"}]
    assert find_workflow_id(workflows, "Daily Briefing") is None


def _mock_exec(output_str, err_str=""):
    """Create a mock SSH exec_command return triple."""
    stdin = MagicMock()
    stdout = MagicMock()
    stdout.read.return_value = output_str.encode()
    stderr = MagicMock()
    stderr.read.return_value = err_str.encode()
    return (stdin, stdout, stderr)


@patch("execute_daily_briefing.get_ssh_client")
def test_main_found_and_executed(mock_get_ssh):
    workflows = [{"name": "Daily Briefing", "id": "wf123"}]
    ssh = MagicMock()
    mock_get_ssh.return_value = ssh
    ssh.exec_command.side_effect = [
        _mock_exec(json.dumps(workflows)),
        _mock_exec("Execution was successful", ""),
    ]
    main()
    assert ssh.exec_command.call_count == 2
    ssh.close.assert_called_once()


@patch("execute_daily_briefing.get_ssh_client")
def test_main_found_with_stderr(mock_get_ssh, capsys):
    workflows = [{"name": "Daily Briefing", "id": "wf123"}]
    ssh = MagicMock()
    mock_get_ssh.return_value = ssh
    ssh.exec_command.side_effect = [
        _mock_exec(json.dumps(workflows)),
        _mock_exec("Execution was successful", "some warning"),
    ]
    main()
    captured = capsys.readouterr()
    assert "ERROR:" in captured.out
    assert "some warning" in captured.out
    ssh.close.assert_called_once()


@patch("execute_daily_briefing.get_ssh_client")
def test_main_workflow_not_found(mock_get_ssh, capsys):
    workflows = [{"name": "Other", "id": "x"}]
    ssh = MagicMock()
    mock_get_ssh.return_value = ssh
    ssh.exec_command.return_value = _mock_exec(json.dumps(workflows))
    main()
    captured = capsys.readouterr()
    assert "not found" in captured.out
    ssh.close.assert_called_once()


@patch("execute_daily_briefing.get_ssh_client")
def test_main_invalid_json(mock_get_ssh, capsys):
    ssh = MagicMock()
    mock_get_ssh.return_value = ssh
    ssh.exec_command.return_value = _mock_exec("not json at all")
    main()
    captured = capsys.readouterr()
    assert "Error parsing JSON" in captured.out
    ssh.close.assert_called_once()
