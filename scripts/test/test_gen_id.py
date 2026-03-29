"""Tests for gen_id() in fase2_deploy.py

gen_id generates random 16-char alphanumeric IDs for workflow nodes.
Since fase2_deploy.py runs SSH commands at module level, we set up
a mock SSH client before importing, then restore the original.
"""
from unittest.mock import MagicMock

# Build a mock SSH client whose exec_command returns (stdin, stdout, stderr)
mock_ssh = MagicMock()
mock_stdout = MagicMock()
mock_stdout.read.return_value = b""
mock_stderr = MagicMock()
mock_stderr.read.return_value = b""
mock_ssh.exec_command.return_value = (MagicMock(), mock_stdout, mock_stderr)

import shared_config  # noqa: E402
_original_get_ssh = shared_config.get_ssh_client
shared_config.get_ssh_client = MagicMock(return_value=mock_ssh)

from deploy.fase2_deploy import gen_id  # noqa: E402

# Restore original so other tests are not affected
shared_config.get_ssh_client = _original_get_ssh


def test_gen_id_returns_string():
    assert isinstance(gen_id(), str)


def test_gen_id_length():
    assert len(gen_id()) == 16


def test_gen_id_alphanumeric():
    assert gen_id().isalnum()


def test_gen_id_unique():
    ids = {gen_id() for _ in range(50)}
    assert len(ids) == 50


def test_gen_id_no_special_chars():
    for _ in range(20):
        result = gen_id()
        assert all(c.isalpha() or c.isdigit() for c in result)
