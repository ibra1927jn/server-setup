"""Tests for create_telegram_ai_bot*.py main() functions with mocked SSH."""
from unittest.mock import MagicMock, patch


def _mock_ssh_basic():
    """SSH mock for v1 bot (no sftp)."""
    ssh = MagicMock()
    call_count = [0]

    def exec_side(cmd):
        call_count[0] += 1
        stdout = MagicMock()
        stderr = MagicMock()
        stderr.read.return_value = b''
        if call_count[0] == 2:
            # wc -c
            stdout.read.return_value = b'1234 /tmp/telegram_ai_bot.json'
        elif call_count[0] == 3:
            # import
            stdout.read.return_value = b'Imported'
        else:
            stdout.read.return_value = b''
        return (MagicMock(), stdout, stderr)

    ssh.exec_command.side_effect = exec_side
    return ssh


def _mock_ssh_sftp():
    """SSH mock for v2/v3 bots (with sftp)."""
    ssh = MagicMock()
    sftp = MagicMock()
    sftp_file = MagicMock()
    sftp_file.__enter__ = MagicMock(return_value=sftp_file)
    sftp_file.__exit__ = MagicMock(return_value=False)
    sftp.file.return_value = sftp_file
    sftp.__enter__ = MagicMock(return_value=sftp)
    sftp.__exit__ = MagicMock(return_value=False)
    ssh.open_sftp.return_value = sftp

    def exec_side(cmd):
        stdout = MagicMock()
        stderr = MagicMock()
        stderr.read.return_value = b''
        stdout.read.return_value = b'OK'
        return (MagicMock(), stdout, stderr)

    ssh.exec_command.side_effect = exec_side
    return ssh


class TestCreateTelegramAiBotV1Main:
    @patch("create_telegram_ai_bot.time.sleep")
    @patch("create_telegram_ai_bot.get_ssh_client")
    def test_main_runs(self, mock_get_ssh, mock_sleep, capsys):
        from create_telegram_ai_bot import main
        ssh = _mock_ssh_basic()
        mock_get_ssh.return_value = ssh
        main()
        out = capsys.readouterr().out
        assert "File size" in out

    @patch("create_telegram_ai_bot.time.sleep")
    @patch("create_telegram_ai_bot.get_ssh_client")
    def test_main_closes_ssh(self, mock_get_ssh, mock_sleep):
        from create_telegram_ai_bot import main
        ssh = _mock_ssh_basic()
        mock_get_ssh.return_value = ssh
        main()
        ssh.close.assert_called_once()

    @patch("create_telegram_ai_bot.time.sleep")
    @patch("create_telegram_ai_bot.get_ssh_client")
    def test_main_imports_workflow(self, mock_get_ssh, mock_sleep):
        from create_telegram_ai_bot import main
        ssh = _mock_ssh_basic()
        mock_get_ssh.return_value = ssh
        main()
        # Should have called exec_command at least 3 times (write, wc, import)
        assert ssh.exec_command.call_count == 3


class TestCreateTelegramAiBotV2Main:
    @patch("create_telegram_ai_bot_v2.time.sleep")
    @patch("create_telegram_ai_bot_v2.get_ssh_client")
    def test_main_runs(self, mock_get_ssh, mock_sleep, capsys):
        from create_telegram_ai_bot_v2 import main
        ssh = _mock_ssh_sftp()
        mock_get_ssh.return_value = ssh
        main()
        out = capsys.readouterr().out
        assert "DONE" in out

    @patch("create_telegram_ai_bot_v2.time.sleep")
    @patch("create_telegram_ai_bot_v2.get_ssh_client")
    def test_main_uses_sftp(self, mock_get_ssh, mock_sleep):
        from create_telegram_ai_bot_v2 import main
        ssh = _mock_ssh_sftp()
        mock_get_ssh.return_value = ssh
        main()
        ssh.open_sftp.assert_called_once()

    @patch("create_telegram_ai_bot_v2.time.sleep")
    @patch("create_telegram_ai_bot_v2.get_ssh_client")
    def test_main_closes_ssh(self, mock_get_ssh, mock_sleep):
        from create_telegram_ai_bot_v2 import main
        ssh = _mock_ssh_sftp()
        mock_get_ssh.return_value = ssh
        main()
        ssh.close.assert_called_once()


class TestCreateTelegramAiBotV3Main:
    @patch("create_telegram_ai_bot_v3.time.sleep")
    @patch("create_telegram_ai_bot_v3.get_ssh_client")
    def test_main_success(self, mock_get_ssh, mock_sleep, capsys):
        from create_telegram_ai_bot_v3 import main
        ssh = _mock_ssh_sftp()

        # v3 checks for "error" in stdout to decide activation
        def exec_side(cmd):
            stdout = MagicMock()
            stderr = MagicMock()
            stderr.read.return_value = b''
            if "import:workflow" in str(cmd):
                stdout.read.return_value = b'imported successfully'
            elif "update:workflow" in str(cmd):
                stdout.read.return_value = b'activated'
            else:
                stdout.read.return_value = b''
            return (MagicMock(), stdout, stderr)

        ssh.exec_command.side_effect = exec_side
        mock_get_ssh.return_value = ssh
        main()
        out = capsys.readouterr().out
        assert "SUCCESS" in out

    @patch("create_telegram_ai_bot_v3.time.sleep")
    @patch("create_telegram_ai_bot_v3.get_ssh_client")
    def test_main_error_skips_activation(self, mock_get_ssh, mock_sleep, capsys):
        from create_telegram_ai_bot_v3 import main
        ssh = _mock_ssh_sftp()

        def exec_side(cmd):
            stdout = MagicMock()
            stderr = MagicMock()
            stderr.read.return_value = b''
            if "import:workflow" in str(cmd):
                stdout.read.return_value = b'Error: workflow already exists'
            else:
                stdout.read.return_value = b''
            return (MagicMock(), stdout, stderr)

        ssh.exec_command.side_effect = exec_side
        mock_get_ssh.return_value = ssh
        main()
        out = capsys.readouterr().out
        assert "SUCCESS" not in out

    @patch("create_telegram_ai_bot_v3.time.sleep")
    @patch("create_telegram_ai_bot_v3.get_ssh_client")
    def test_main_closes_ssh(self, mock_get_ssh, mock_sleep):
        from create_telegram_ai_bot_v3 import main
        ssh = _mock_ssh_sftp()
        mock_get_ssh.return_value = ssh
        main()
        ssh.close.assert_called_once()
