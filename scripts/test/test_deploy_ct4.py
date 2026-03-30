"""Tests for deploy/deploy_ct4.py deploy() function"""
from unittest.mock import MagicMock, patch
import os


def _mock_ssh(stdout="", stderr=""):
    """Create a mock SSH client that returns given stdout/stderr."""
    ssh = MagicMock()
    o = MagicMock()
    o.read.return_value = stdout.encode()
    e = MagicMock()
    e.read.return_value = stderr.encode()
    ssh.exec_command.return_value = (MagicMock(), o, e)
    return ssh


def test_skip_set_excludes_sensitive_dirs():
    """SKIP should exclude .git, venv, .env, etc."""
    from deploy.deploy_ct4 import SKIP

    assert ".git" in SKIP
    assert "venv" in SKIP
    assert ".env" in SKIP
    assert "__pycache__" in SKIP
    assert "node_modules" in SKIP


@patch("deploy.deploy_ct4.os.path.getsize", return_value=100)
@patch("deploy.deploy_ct4.os.walk")
@patch("deploy.deploy_ct4.get_ssh_client")
def test_deploy_creates_remote_dir_if_missing(mock_get_ssh, mock_walk, mock_size):
    """deploy() should create REMOTE_DIR if it doesn't exist."""
    from deploy.deploy_ct4 import deploy

    ssh = _mock_ssh(stdout="ok")
    sftp = MagicMock()
    sftp.stat.side_effect = FileNotFoundError  # dir doesn't exist
    ssh.open_sftp.return_value = sftp
    mock_get_ssh.return_value = ssh
    mock_walk.return_value = []  # no files to upload

    deploy()

    sftp.mkdir.assert_called()


@patch("deploy.deploy_ct4.os.path.getsize", return_value=100)
@patch("deploy.deploy_ct4.os.walk")
@patch("deploy.deploy_ct4.get_ssh_client")
def test_deploy_skips_mkdir_if_exists(mock_get_ssh, mock_walk, mock_size):
    """deploy() should not create REMOTE_DIR if it already exists."""
    from deploy.deploy_ct4 import deploy

    ssh = _mock_ssh(stdout="ok")
    sftp = MagicMock()
    sftp.stat.return_value = MagicMock()  # dir exists
    ssh.open_sftp.return_value = sftp
    mock_get_ssh.return_value = ssh
    mock_walk.return_value = []

    deploy()

    sftp.mkdir.assert_not_called()


@patch("deploy.deploy_ct4.os.path.getsize", return_value=500)
@patch("deploy.deploy_ct4.os.walk")
@patch("deploy.deploy_ct4.get_ssh_client")
@patch("deploy.deploy_ct4.LOCAL_DIR", "/fake/local")
@patch("deploy.deploy_ct4.REMOTE_DIR", "/root/bot")
def test_deploy_uploads_files(mock_get_ssh, mock_walk, mock_size):
    """deploy() should upload files to the remote server."""
    from deploy.deploy_ct4 import deploy

    ssh = _mock_ssh(stdout="ok")
    sftp = MagicMock()
    sftp.stat.return_value = MagicMock()  # dirs exist
    ssh.open_sftp.return_value = sftp
    mock_get_ssh.return_value = ssh

    # Simulate one directory with one file
    mock_walk.return_value = [
        ("/fake/local", [], ["main.py"]),
    ]

    deploy()

    sftp.put.assert_called_once_with(
        os.path.join("/fake/local", "main.py"),
        "/root/bot/main.py",
    )


@patch("deploy.deploy_ct4.os.path.getsize", return_value=100)
@patch("deploy.deploy_ct4.os.walk")
@patch("deploy.deploy_ct4.get_ssh_client")
@patch("deploy.deploy_ct4.LOCAL_DIR", "/fake/local")
@patch("deploy.deploy_ct4.REMOTE_DIR", "/root/bot")
def test_deploy_creates_subdir_when_missing(mock_get_ssh, mock_walk, mock_size):
    """deploy() should call _mkdir_p for subdirs that don't exist on remote."""
    from deploy.deploy_ct4 import deploy

    ssh = _mock_ssh(stdout="ok")
    sftp = MagicMock()

    def stat_side_effect(path):
        # Subdir /root/bot/sub doesn't exist; everything else does
        if path == "/root/bot/sub":
            raise FileNotFoundError
        return MagicMock()

    sftp.stat.side_effect = stat_side_effect
    ssh.open_sftp.return_value = sftp
    mock_get_ssh.return_value = ssh

    mock_walk.return_value = [
        ("/fake/local", ["sub"], ["a.py"]),
        ("/fake/local/sub", [], ["b.py"]),
    ]

    deploy()

    # Should have uploaded both files and created the subdir
    assert sftp.put.call_count == 2
    sftp.mkdir.assert_called_with("/root/bot/sub")


@patch("deploy.deploy_ct4.os.path.getsize", return_value=11 * 1024 * 1024)
@patch("deploy.deploy_ct4.os.walk")
@patch("deploy.deploy_ct4.get_ssh_client")
@patch("deploy.deploy_ct4.LOCAL_DIR", "/fake/local")
@patch("deploy.deploy_ct4.REMOTE_DIR", "/root/bot")
def test_deploy_skips_large_files(mock_get_ssh, mock_walk, mock_size, capsys):
    """deploy() should skip files larger than 10MB."""
    from deploy.deploy_ct4 import deploy

    ssh = _mock_ssh(stdout="ok")
    sftp = MagicMock()
    sftp.stat.return_value = MagicMock()
    ssh.open_sftp.return_value = sftp
    mock_get_ssh.return_value = ssh

    mock_walk.return_value = [
        ("/fake/local", [], ["huge.bin"]),
    ]

    deploy()

    sftp.put.assert_not_called()
    captured = capsys.readouterr()
    assert "SKIP (>10MB)" in captured.out


@patch("deploy.deploy_ct4.os.path.getsize", return_value=100)
@patch("deploy.deploy_ct4.os.walk")
@patch("deploy.deploy_ct4.get_ssh_client")
@patch("deploy.deploy_ct4.LOCAL_DIR", "/fake/local")
def test_deploy_closes_connections(mock_get_ssh, mock_walk, mock_size):
    """deploy() should close SFTP and SSH connections."""
    from deploy.deploy_ct4 import deploy

    ssh = _mock_ssh(stdout="ok")
    sftp = MagicMock()
    sftp.stat.return_value = MagicMock()
    ssh.open_sftp.return_value = sftp
    mock_get_ssh.return_value = ssh
    mock_walk.return_value = []

    deploy()

    sftp.close.assert_called_once()
    ssh.close.assert_called_once()


@patch("deploy.deploy_ct4.os.path.getsize", return_value=100)
@patch("deploy.deploy_ct4.os.walk")
@patch("deploy.deploy_ct4.get_ssh_client")
@patch("deploy.deploy_ct4.LOCAL_DIR", "/fake/local")
def test_deploy_runs_pip_install(mock_get_ssh, mock_walk, mock_size):
    """deploy() should run pip install on the remote server."""
    from deploy.deploy_ct4 import deploy

    ssh = _mock_ssh(stdout="ok")
    sftp = MagicMock()
    sftp.stat.return_value = MagicMock()
    ssh.open_sftp.return_value = sftp
    mock_get_ssh.return_value = ssh
    mock_walk.return_value = []

    deploy()

    cmds = [c[0][0] for c in ssh.exec_command.call_args_list]
    assert any("pip3 install" in c for c in cmds)
