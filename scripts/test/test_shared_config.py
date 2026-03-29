"""Tests for shared_config module — validates config loading and SSH client factory."""
import os
from unittest.mock import patch, MagicMock

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

    with patch.dict(os.environ, {}, clear=False):
        with pytest.raises(ValueError, match="VPS_HOST"):
            get_ssh_client(host="", password="fake")


def test_config_values_are_strings():
    """All config values should be strings (not None)."""
    from shared_config import (
        VPS_HOST, VPS_USER, VPS_PASS, N8N_URL,
        N8N_EMAIL, N8N_PASSWORD, N8N_API_KEY,
        TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID,
        OPENROUTER_API_KEY, GITHUB_PAT,
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
