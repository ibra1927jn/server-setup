"""Tests for export_analyze_workflow.py main() with mocked SSH."""
import json
from unittest.mock import MagicMock, patch

from export_analyze_workflow import main


def _mock_ssh_with_response(wf_response):
    """Build a mock SSH client that returns wf_response on the second exec_command."""
    ssh = MagicMock()
    call_count = [0]

    def exec_side_effect(cmd):
        call_count[0] += 1
        stdout = MagicMock()
        stderr = MagicMock()
        if call_count[0] == 1:
            # login response
            stdout.read.return_value = b'{"id":"user1"}'
        else:
            # workflow export response
            stdout.read.return_value = json.dumps(wf_response).encode()
        return (MagicMock(), stdout, stderr)

    ssh.exec_command.side_effect = exec_side_effect
    return ssh


class TestExportAnalyzeMain:
    @patch("export_analyze_workflow.time.sleep")
    @patch("export_analyze_workflow.get_ssh_client")
    def test_main_runs_with_data_wrapper(self, mock_get_ssh, mock_sleep, capsys):
        wf = {
            "data": {
                "name": "Test WF",
                "nodes": [
                    {"name": "Trigger", "type": "telegramTrigger", "typeVersion": 1},
                    {"name": "Agent", "type": "langchain.agent", "typeVersion": 1.6},
                ],
                "connections": {
                    "Trigger": {"main": [[{"node": "Agent", "type": "main", "index": 0}]]},
                },
            }
        }
        mock_get_ssh.return_value = _mock_ssh_with_response(wf)
        main()
        out = capsys.readouterr().out
        assert "Trigger" in out
        assert "Agent" in out

    @patch("export_analyze_workflow.time.sleep")
    @patch("export_analyze_workflow.get_ssh_client")
    def test_main_runs_with_flat_response(self, mock_get_ssh, mock_sleep, capsys):
        wf = {
            "name": "Flat WF",
            "nodes": [{"name": "Start", "type": "start", "typeVersion": 1}],
            "connections": {},
        }
        mock_get_ssh.return_value = _mock_ssh_with_response(wf)
        main()
        out = capsys.readouterr().out
        assert "Start" in out

    @patch("export_analyze_workflow.time.sleep")
    @patch("export_analyze_workflow.get_ssh_client")
    def test_main_empty_nodes(self, mock_get_ssh, mock_sleep, capsys):
        wf = {"data": {"name": "Empty", "nodes": [], "connections": {}}}
        mock_get_ssh.return_value = _mock_ssh_with_response(wf)
        main()
        out = capsys.readouterr().out
        assert "Nodes in workflow" in out

    @patch("export_analyze_workflow.time.sleep")
    @patch("export_analyze_workflow.get_ssh_client")
    def test_main_login_fail_still_exports(self, mock_get_ssh, mock_sleep, capsys):
        """Login result is printed but export still runs."""
        ssh = MagicMock()
        call_count = [0]

        def exec_side(cmd):
            call_count[0] += 1
            stdout = MagicMock()
            if call_count[0] == 1:
                stdout.read.return_value = b'{"error":"bad creds"}'
            else:
                stdout.read.return_value = json.dumps({
                    "data": {"name": "WF", "nodes": [], "connections": {}}
                }).encode()
            return (MagicMock(), stdout, MagicMock())

        ssh.exec_command.side_effect = exec_side
        mock_get_ssh.return_value = ssh
        main()
        out = capsys.readouterr().out
        assert "FAIL" in out

    @patch("export_analyze_workflow.time.sleep")
    @patch("export_analyze_workflow.get_ssh_client")
    def test_main_closes_ssh(self, mock_get_ssh, mock_sleep):
        wf = {"data": {"name": "WF", "nodes": [], "connections": {}}}
        ssh = _mock_ssh_with_response(wf)
        mock_get_ssh.return_value = ssh
        main()
        ssh.close.assert_called_once()

    @patch("export_analyze_workflow.time.sleep")
    @patch("export_analyze_workflow.get_ssh_client")
    def test_main_prints_connections(self, mock_get_ssh, mock_sleep, capsys):
        wf = {
            "data": {
                "name": "WF",
                "nodes": [{"name": "A", "type": "t", "typeVersion": 1}],
                "connections": {"A": {"main": [[{"node": "B"}]]}},
            }
        }
        mock_get_ssh.return_value = _mock_ssh_with_response(wf)
        main()
        out = capsys.readouterr().out
        assert "Connections" in out

    @patch("export_analyze_workflow.time.sleep")
    @patch("export_analyze_workflow.get_ssh_client")
    def test_main_node_without_typeversion(self, mock_get_ssh, mock_sleep, capsys):
        wf = {
            "data": {
                "name": "WF",
                "nodes": [{"name": "X", "type": "test"}],
                "connections": {},
            }
        }
        mock_get_ssh.return_value = _mock_ssh_with_response(wf)
        main()
        out = capsys.readouterr().out
        assert "typeVersion: None" in out
