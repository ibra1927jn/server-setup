"""Tests for _mkdir_p() in deploy/deploy_ct4.py"""

from unittest.mock import MagicMock

from deploy.deploy_ct4 import _mkdir_p


def test_creates_single_dir():
    sftp = MagicMock()
    sftp.stat.side_effect = FileNotFoundError
    _mkdir_p(sftp, "/root")
    sftp.mkdir.assert_called_with("/root")


def test_creates_nested_dirs():
    sftp = MagicMock()
    sftp.stat.side_effect = FileNotFoundError
    _mkdir_p(sftp, "/root/app/data")
    assert sftp.mkdir.call_count == 3
    sftp.mkdir.assert_any_call("/root")
    sftp.mkdir.assert_any_call("/root/app")
    sftp.mkdir.assert_any_call("/root/app/data")


def test_skips_existing_dirs():
    sftp = MagicMock()
    # All dirs exist (stat succeeds)
    sftp.stat.return_value = MagicMock()
    _mkdir_p(sftp, "/root/app")
    sftp.mkdir.assert_not_called()


def test_mixed_existing_and_new():
    sftp = MagicMock()
    # /root exists, /root/newdir does not

    def stat_side_effect(path):
        if path == "/root":
            return MagicMock()
        raise FileNotFoundError

    sftp.stat.side_effect = stat_side_effect
    _mkdir_p(sftp, "/root/newdir")
    sftp.mkdir.assert_called_once_with("/root/newdir")


def test_handles_root_path():
    sftp = MagicMock()
    sftp.stat.return_value = MagicMock()
    _mkdir_p(sftp, "/")
    sftp.mkdir.assert_not_called()
