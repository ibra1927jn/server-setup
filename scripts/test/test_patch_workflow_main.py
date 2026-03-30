"""Tests for patch_workflow.py main() with mocked SSH."""
import json
from unittest.mock import MagicMock, patch

from patch_workflow import main


def _make_mock_ssh(wf_data=None):
    """Build mock SSH for patch_workflow main()."""
    if wf_data is None:
        wf_data = {
            "data": {
                "id": "wf123",
                "name": "AI Agent Base",
                "nodes": [
                    {"name": "Telegram Trigger", "type": "telegramTrigger",
                     "typeVersion": 1},
                    {"name": "AI Agent1", "type": "@n8n/n8n-nodes-langchain.agent",
                     "typeVersion": 1.6},
                    {"name": "OpenAI Chat Model",
                     "type": "@n8n/n8n-nodes-langchain.lmChatOpenAi",
                     "typeVersion": 1, "parameters": {"model": "old"}},
                ],
                "connections": {
                    "OpenAI Chat Model": {"ai_languageModel": [[
                        {"node": "AI Agent1", "type": "ai_languageModel", "index": 0}
                    ]]},
                },
                "active": False,
            }
        }

    ssh = MagicMock()
    sftp = MagicMock()
    # sftp.file returns a context-manager-like mock
    sftp_file = MagicMock()
    sftp_file.__enter__ = MagicMock(return_value=sftp_file)
    sftp_file.__exit__ = MagicMock(return_value=False)
    sftp.file.return_value = sftp_file
    ssh.open_sftp.return_value = sftp

    call_idx = [0]

    def exec_side(cmd):
        idx = call_idx[0]
        call_idx[0] += 1
        stdout = MagicMock()
        stderr = MagicMock()
        stderr.read.return_value = b''
        if idx == 0:
            # login
            stdout.read.return_value = b'{"id":"u1"}'
        elif idx == 1:
            # download workflow
            stdout.read.return_value = json.dumps(wf_data).encode()
        elif idx == 2:
            # upload response
            result = json.dumps({"data": {"id": "wf123"}})
            stdout.read.return_value = result.encode()
        else:
            stdout.read.return_value = b''
        return (MagicMock(), stdout, stderr)

    ssh.exec_command.side_effect = exec_side
    return ssh


class TestPatchWorkflowMain:
    @patch("patch_workflow.time.sleep")
    @patch("patch_workflow.get_ssh_client")
    def test_main_patches_and_uploads(self, mock_get_ssh, mock_sleep, capsys):
        ssh = _make_mock_ssh()
        mock_get_ssh.return_value = ssh
        main()
        out = capsys.readouterr().out
        assert "Logging in" in out or "Downloading" in out or "Modifying" in out

    @patch("patch_workflow.time.sleep")
    @patch("patch_workflow.get_ssh_client")
    def test_main_closes_ssh(self, mock_get_ssh, mock_sleep):
        ssh = _make_mock_ssh()
        mock_get_ssh.return_value = ssh
        main()
        ssh.close.assert_called_once()

    @patch("patch_workflow.time.sleep")
    @patch("patch_workflow.get_ssh_client")
    def test_main_opens_sftp(self, mock_get_ssh, mock_sleep):
        ssh = _make_mock_ssh()
        mock_get_ssh.return_value = ssh
        main()
        ssh.open_sftp.assert_called_once()

    @patch("patch_workflow.time.sleep")
    @patch("patch_workflow.get_ssh_client")
    def test_main_writes_patched_json(self, mock_get_ssh, mock_sleep):
        ssh = _make_mock_ssh()
        mock_get_ssh.return_value = ssh
        main()
        sftp = ssh.open_sftp.return_value
        sftp.file.assert_called_once_with('/tmp/wf_patch.json', 'w')

    @patch("patch_workflow.time.sleep")
    @patch("patch_workflow.get_ssh_client")
    def test_main_handles_json_decode_error(self, mock_get_ssh, mock_sleep, capsys):
        """When upload response is not valid JSON, prints error."""
        ssh = MagicMock()
        sftp = MagicMock()
        sftp_file = MagicMock()
        sftp_file.__enter__ = MagicMock(return_value=sftp_file)
        sftp_file.__exit__ = MagicMock(return_value=False)
        sftp.file.return_value = sftp_file
        ssh.open_sftp.return_value = sftp

        wf_data = {
            "data": {
                "name": "WF", "nodes": [
                    {"name": "OpenAI Chat Model", "type": "lmChatOpenAi",
                     "typeVersion": 1, "parameters": {}},
                ],
                "connections": {"OpenAI Chat Model": {}}, "active": False,
            }
        }
        call_idx = [0]

        def exec_side(cmd):
            idx = call_idx[0]
            call_idx[0] += 1
            stdout = MagicMock()
            stderr = MagicMock()
            stderr.read.return_value = b''
            if idx == 1:
                stdout.read.return_value = json.dumps(wf_data).encode()
            elif idx == 2:
                stdout.read.return_value = b'not-json'
            else:
                stdout.read.return_value = b'{}'
            return (MagicMock(), stdout, stderr)

        ssh.exec_command.side_effect = exec_side
        mock_get_ssh.return_value = ssh
        main()
        out = capsys.readouterr().out
        assert "Failed to decode JSON" in out

    @patch("patch_workflow.time.sleep")
    @patch("patch_workflow.get_ssh_client")
    def test_main_prints_patched_id(self, mock_get_ssh, mock_sleep, capsys):
        ssh = _make_mock_ssh()
        mock_get_ssh.return_value = ssh
        main()
        out = capsys.readouterr().out
        assert "wf123" in out
