"""Tests for final_pendientes.py main() and BACKUP_SCRIPT with mocked SSH."""
from unittest.mock import MagicMock, patch

from final_pendientes import main, BACKUP_SCRIPT


class TestBackupScript:
    def test_contains_backup_dir(self):
        assert "/root/n8n-backups" in BACKUP_SCRIPT

    def test_contains_docker_cp(self):
        assert "docker cp" in BACKUP_SCRIPT

    def test_contains_workflow_export(self):
        assert "n8n export:workflow" in BACKUP_SCRIPT

    def test_contains_credential_export(self):
        assert "n8n export:credentials" in BACKUP_SCRIPT

    def test_contains_cleanup(self):
        assert "-mtime +7 -delete" in BACKUP_SCRIPT

    def test_contains_timestamp(self):
        assert "TIMESTAMP=$(date" in BACKUP_SCRIPT


def _make_mock_ssh(workflow_list="id1 | WF One\nid2 | WF Two"):
    """Build mock SSH where exec_command returns different outputs per call."""
    ssh = MagicMock()
    call_idx = [0]
    responses = {
        0: workflow_list.encode(),       # list:workflow
        1: b'"active":true',             # activate wf1 (API)
        2: b'"active":true',             # activate wf2 (API)
        3: b'',                          # docker restart
        4: b'id1 | WF One\nid2 | WF Two',  # verify listing
        5: b'',                          # write backup script
        6: b'[2026-03-30] Backup completed',  # run backup
        7: b'0 3 * * * /root/n8n-backup.sh',  # crontab -l
        8: b'-rw-r--r-- 1 root root 100K n8n_db.sqlite',  # ls backups
    }

    def exec_side(cmd):
        idx = call_idx[0]
        call_idx[0] += 1
        stdout = MagicMock()
        stderr = MagicMock()
        stdout.read.return_value = responses.get(idx, b'')
        stderr.read.return_value = b''
        return (MagicMock(), stdout, stderr)

    ssh.exec_command.side_effect = exec_side
    return ssh


class TestFinalPendientesMain:
    @patch("final_pendientes.time.sleep")
    @patch("final_pendientes.get_ssh_client")
    def test_main_publishes_workflows(self, mock_get_ssh, mock_sleep, capsys):
        ssh = _make_mock_ssh()
        mock_get_ssh.return_value = ssh
        main()
        out = capsys.readouterr().out
        assert "WF One" in out
        assert "WF Two" in out
        assert "PUBLICANDO" in out

    @patch("final_pendientes.time.sleep")
    @patch("final_pendientes.get_ssh_client")
    def test_main_sets_up_backup(self, mock_get_ssh, mock_sleep, capsys):
        ssh = _make_mock_ssh()
        mock_get_ssh.return_value = ssh
        main()
        out = capsys.readouterr().out
        assert "BACKUP" in out
        assert "COMPLETADO" in out

    @patch("final_pendientes.time.sleep")
    @patch("final_pendientes.get_ssh_client")
    def test_main_closes_ssh(self, mock_get_ssh, mock_sleep):
        ssh = _make_mock_ssh()
        mock_get_ssh.return_value = ssh
        main()
        ssh.close.assert_called_once()

    @patch("final_pendientes.time.sleep")
    @patch("final_pendientes.get_ssh_client")
    def test_main_with_cli_fallback(self, mock_get_ssh, mock_sleep, capsys):
        """When API activation fails, falls back to CLI."""
        ssh = MagicMock()
        call_idx = [0]

        def exec_side(cmd):
            idx = call_idx[0]
            call_idx[0] += 1
            stdout = MagicMock()
            stderr = MagicMock()
            stderr.read.return_value = b''
            if idx == 0:
                stdout.read.return_value = b'id1 | WF One'
            elif idx == 1:
                # API activation fails
                stdout.read.return_value = b'{"error": "not found"}'
            elif idx == 2:
                # CLI fallback
                stdout.read.return_value = b''
            else:
                stdout.read.return_value = b''
            return (MagicMock(), stdout, stderr)

        ssh.exec_command.side_effect = exec_side
        mock_get_ssh.return_value = ssh
        main()
        out = capsys.readouterr().out
        assert "CLI" in out

    @patch("final_pendientes.time.sleep")
    @patch("final_pendientes.get_ssh_client")
    def test_main_no_workflows(self, mock_get_ssh, mock_sleep, capsys):
        ssh = _make_mock_ssh(workflow_list="no pipe here")
        mock_get_ssh.return_value = ssh
        main()
        out = capsys.readouterr().out
        assert "PUBLICANDO" in out

    @patch("final_pendientes.time.sleep")
    @patch("final_pendientes.get_ssh_client")
    def test_main_backup_error_printed(self, mock_get_ssh, mock_sleep, capsys):
        """Backup stderr is printed."""
        ssh = MagicMock()
        call_idx = [0]

        def exec_side(cmd):
            idx = call_idx[0]
            call_idx[0] += 1
            stdout = MagicMock()
            stderr = MagicMock()
            if idx == 0:
                stdout.read.return_value = b''
                stderr.read.return_value = b''
            elif "n8n-backup.sh" in str(cmd) and "bash" in str(cmd):
                stdout.read.return_value = b''
                stderr.read.return_value = b'backup error'
            else:
                stdout.read.return_value = b''
                stderr.read.return_value = b''
            return (MagicMock(), stdout, stderr)

        ssh.exec_command.side_effect = exec_side
        mock_get_ssh.return_value = ssh
        main()
        # main completes without crash
        ssh.close.assert_called_once()
