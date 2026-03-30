"""Tests for upgrade_agent_node.py main() with mocked SSH."""
import json
from unittest.mock import MagicMock, mock_open, patch

from upgrade_agent_node import main


def _make_wf():
    return {
        "name": "AI Agent Base",
        "nodes": [
            {"name": "Trigger", "type": "n8n-nodes-base.telegramTrigger",
             "typeVersion": 1},
            {"name": "AI Agent1", "type": "@n8n/n8n-nodes-langchain.agent",
             "typeVersion": 1.6},
            {"name": "Chat Model", "type": "@n8n/n8n-nodes-langchain.lmChatOpenAi",
             "typeVersion": 1},
        ],
    }


def _make_mock_ssh(wf=None, *, as_list=False):
    if wf is None:
        wf = _make_wf()
    export_data = [wf] if as_list else wf

    ssh = MagicMock()
    sftp = MagicMock()
    ssh.open_sftp.return_value = sftp

    call_idx = [0]

    def exec_side(cmd):
        idx = call_idx[0]
        call_idx[0] += 1
        stdout = MagicMock()
        stderr = MagicMock()
        stderr.read.return_value = b''
        if idx == 0:
            # export workflow
            stdout.read.return_value = json.dumps(export_data).encode()
        elif idx == 1:
            # docker cp
            stdout.read.return_value = b''
        elif idx == 2:
            # import
            stdout.read.return_value = b'Imported workflow'
        elif idx == 3:
            # restart
            stdout.read.return_value = b''
        elif idx == 4:
            # list workflows
            stdout.read.return_value = b'id1 | AI Agent Base'
        return (MagicMock(), stdout, stderr)

    ssh.exec_command.side_effect = exec_side
    return ssh


class TestUpgradeAgentMain:
    @patch("builtins.open", mock_open())
    @patch("upgrade_agent_node.time.sleep")
    @patch("upgrade_agent_node.get_ssh_client")
    def test_main_upgrades_agent(self, mock_get_ssh, mock_sleep, capsys):
        ssh = _make_mock_ssh()
        mock_get_ssh.return_value = ssh
        main()
        out = capsys.readouterr().out
        assert "Exporting" in out or "Importing" in out

    @patch("builtins.open", mock_open())
    @patch("upgrade_agent_node.time.sleep")
    @patch("upgrade_agent_node.get_ssh_client")
    def test_main_closes_ssh_and_sftp(self, mock_get_ssh, mock_sleep):
        ssh = _make_mock_ssh()
        mock_get_ssh.return_value = ssh
        main()
        ssh.close.assert_called_once()
        ssh.open_sftp.return_value.close.assert_called_once()

    @patch("builtins.open", mock_open())
    @patch("upgrade_agent_node.time.sleep")
    @patch("upgrade_agent_node.get_ssh_client")
    def test_main_uploads_via_sftp(self, mock_get_ssh, mock_sleep):
        ssh = _make_mock_ssh()
        mock_get_ssh.return_value = ssh
        main()
        sftp = ssh.open_sftp.return_value
        sftp.put.assert_called_once()

    @patch("builtins.open", mock_open())
    @patch("upgrade_agent_node.time.sleep")
    @patch("upgrade_agent_node.get_ssh_client")
    def test_main_with_list_format(self, mock_get_ssh, mock_sleep, capsys):
        ssh = _make_mock_ssh(as_list=True)
        mock_get_ssh.return_value = ssh
        main()
        out = capsys.readouterr().out
        assert "AI Agent Base" in out

    @patch("builtins.open", mock_open())
    @patch("upgrade_agent_node.time.sleep")
    @patch("upgrade_agent_node.get_ssh_client")
    def test_main_no_agent_exits(self, mock_get_ssh, mock_sleep):
        """When no agent node exists, main should call exit(1)."""
        wf = {"name": "No Agent", "nodes": [
            {"name": "Trigger", "type": "start", "typeVersion": 1},
        ]}
        ssh = _make_mock_ssh(wf=wf)
        mock_get_ssh.return_value = ssh
        import pytest
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1

    @patch("builtins.open", mock_open())
    @patch("upgrade_agent_node.time.sleep")
    @patch("upgrade_agent_node.get_ssh_client")
    def test_main_prints_stderr(self, mock_get_ssh, mock_sleep, capsys):
        """When export has stderr, it's printed."""
        ssh = MagicMock()
        sftp = MagicMock()
        ssh.open_sftp.return_value = sftp

        wf = _make_wf()
        call_idx = [0]

        def exec_side(cmd):
            idx = call_idx[0]
            call_idx[0] += 1
            stdout = MagicMock()
            stderr = MagicMock()
            if idx == 0:
                stdout.read.return_value = json.dumps(wf).encode()
                stderr.read.return_value = b'some warning'
            else:
                stdout.read.return_value = b''
                stderr.read.return_value = b''
            return (MagicMock(), stdout, stderr)

        ssh.exec_command.side_effect = exec_side
        mock_get_ssh.return_value = ssh
        main()
        out = capsys.readouterr().out
        assert "some warning" in out

    @patch("builtins.open", mock_open())
    @patch("upgrade_agent_node.time.sleep")
    @patch("upgrade_agent_node.get_ssh_client")
    def test_main_prints_node_info(self, mock_get_ssh, mock_sleep, capsys):
        ssh = _make_mock_ssh()
        mock_get_ssh.return_value = ssh
        main()
        out = capsys.readouterr().out
        assert "Trigger" in out
        assert "AI Agent1" in out
        assert "Chat Model" in out
