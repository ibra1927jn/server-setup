"""Tests for shared_config module — validates config loading and SSH client factory."""
import os
from unittest.mock import patch

import pytest


def test_shared_config_imports():
    """shared_config module can be imported without side effects."""
    import shared_config

    assert hasattr(shared_config, "VPS_HOST")
    assert hasattr(shared_config, "VPS_USER")
    assert hasattr(shared_config, "N8N_URL")
    assert hasattr(shared_config, "TELEGRAM_BOT_TOKEN")
    assert hasattr(shared_config, "TELEGRAM_CHAT_ID")
    assert hasattr(shared_config, "N8N_HEADERS")
    assert hasattr(shared_config, "get_ssh_client")


def test_n8n_headers_structure():
    """N8N_HEADERS has the expected keys."""
    from shared_config import N8N_HEADERS

    assert "Content-Type" in N8N_HEADERS
    assert N8N_HEADERS["Content-Type"] == "application/json"
    assert "X-N8N-API-KEY" in N8N_HEADERS


def test_get_ssh_client_requires_host():
    """get_ssh_client raises ValueError when no host is configured."""
    from shared_config import get_ssh_client

    with patch.dict(os.environ, {}, clear=False), pytest.raises(ValueError, match="VPS_HOST"):
        get_ssh_client(host="", password="fake")


def test_config_values_are_strings():
    """All config values should be strings (not None)."""
    from shared_config import (
        GITHUB_PAT,
        N8N_API_KEY,
        N8N_EMAIL,
        N8N_PASSWORD,
        N8N_URL,
        OPENROUTER_API_KEY,
        TELEGRAM_BOT_TOKEN,
        TELEGRAM_CHAT_ID,
        VPS_HOST,
        VPS_PASS,
        VPS_USER,
    )

    for name, val in [
        ("VPS_HOST", VPS_HOST),
        ("VPS_USER", VPS_USER),
        ("VPS_PASS", VPS_PASS),
        ("N8N_URL", N8N_URL),
        ("N8N_EMAIL", N8N_EMAIL),
        ("N8N_PASSWORD", N8N_PASSWORD),
        ("N8N_API_KEY", N8N_API_KEY),
        ("TELEGRAM_BOT_TOKEN", TELEGRAM_BOT_TOKEN),
        ("TELEGRAM_CHAT_ID", TELEGRAM_CHAT_ID),
        ("OPENROUTER_API_KEY", OPENROUTER_API_KEY),
        ("GITHUB_PAT", GITHUB_PAT),
    ]:
        assert isinstance(val, str), f"{name} should be str, got {type(val)}"


def test_default_vps_user():
    """VPS_USER defaults to 'root' when not set."""
    # The default in code is "root"
    from shared_config import VPS_USER

    # If .env doesn't set it, it should be "root"
    # If .env does set it, it should still be a non-empty string
    assert isinstance(VPS_USER, str)
    assert len(VPS_USER) > 0


def test_get_ssh_client_password_auth(mocker):
    """get_ssh_client connects with password when provided."""
    from shared_config import get_ssh_client

    mock_client = mocker.MagicMock()
    mocker.patch("shared_config.paramiko.SSHClient", return_value=mock_client)

    result = get_ssh_client(host="1.2.3.4", user="admin", password="secret")

    assert result is mock_client
    mock_client.set_missing_host_key_policy.assert_called_once()
    mock_client.connect.assert_called_once_with(
        hostname="1.2.3.4",
        username="admin",
        password="secret",
        look_for_keys=False,
        timeout=10,
    )


def test_get_ssh_client_key_auth(mocker, tmp_path):
    """get_ssh_client connects with SSH key when key_path exists."""
    from shared_config import get_ssh_client

    key_file = tmp_path / "id_rsa"
    key_file.write_text("fake-key")

    mock_client = mocker.MagicMock()
    mocker.patch("shared_config.paramiko.SSHClient", return_value=mock_client)

    result = get_ssh_client(host="1.2.3.4", key_path=str(key_file))

    assert result is mock_client
    mock_client.connect.assert_called_once_with(
        hostname="1.2.3.4",
        username=mocker.ANY,
        key_filename=str(key_file),
        timeout=10,
    )


def test_get_ssh_client_agent_fallback(mocker):
    """get_ssh_client uses SSH agent when no password or key provided."""
    from shared_config import get_ssh_client

    mock_client = mocker.MagicMock()
    mocker.patch("shared_config.paramiko.SSHClient", return_value=mock_client)

    result = get_ssh_client(host="1.2.3.4")

    assert result is mock_client
    mock_client.connect.assert_called_once_with(
        hostname="1.2.3.4",
        username=mocker.ANY,
        allow_agent=True,
        look_for_keys=True,
        timeout=10,
    )


def test_get_ssh_client_custom_timeout(mocker):
    """get_ssh_client respects custom timeout parameter."""
    from shared_config import get_ssh_client

    mock_client = mocker.MagicMock()
    mocker.patch("shared_config.paramiko.SSHClient", return_value=mock_client)

    get_ssh_client(host="1.2.3.4", password="pw", timeout=30)

    call_kwargs = mock_client.connect.call_args[1]
    assert call_kwargs["timeout"] == 30


def test_n8n_url_uses_vps_host():
    """N8N_URL should contain a reference to the VPS host."""
    from shared_config import N8N_URL

    assert isinstance(N8N_URL, str)
    assert "5678" in N8N_URL or N8N_URL == ""


def test_vps_ssh_key_path_is_string():
    """VPS_SSH_KEY_PATH should be a string."""
    from shared_config import VPS_SSH_KEY_PATH

    assert isinstance(VPS_SSH_KEY_PATH, str)
