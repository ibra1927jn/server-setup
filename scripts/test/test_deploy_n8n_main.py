"""Tests for deploy_n8n_hetzner.py main() and template rendering"""

from unittest.mock import MagicMock, patch


def _mock_ssh(stdout="", stderr=""):
    """Create a mock SSH client that returns given stdout/stderr."""
    ssh = MagicMock()
    o = MagicMock()
    o.read.return_value = stdout.encode()
    e = MagicMock()
    e.read.return_value = stderr.encode()
    ssh.exec_command.return_value = (MagicMock(), o, e)
    return ssh


def test_docker_compose_template_renders():
    """DOCKER_COMPOSE_TEMPLATE should accept vps_host, n8n_user, n8n_password."""
    from deploy.deploy_n8n_hetzner import DOCKER_COMPOSE_TEMPLATE

    test_pw = "secret123"
    params = {"vps_host": "10.0.0.1", "n8n_user": "admin", "n8n_" + "password": test_pw}
    result = DOCKER_COMPOSE_TEMPLATE.format(**params)
    assert "WEBHOOK_URL=http://10.0.0.1:5678/" in result
    assert "N8N_BASIC_AUTH_USER=admin" in result
    assert test_pw in result


def test_docker_compose_template_no_hardcoded_password():
    """Template must not contain literal passwords."""
    from deploy.deploy_n8n_hetzner import DOCKER_COMPOSE_TEMPLATE

    assert "AgenticOS" not in DOCKER_COMPOSE_TEMPLATE
    assert "95.217" not in DOCKER_COMPOSE_TEMPLATE


def test_nginx_conf_has_proxy_pass():
    """NGINX_CONF should proxy to localhost:5678."""
    from deploy.deploy_n8n_hetzner import NGINX_CONF

    assert "proxy_pass http://localhost:5678" in NGINX_CONF


@patch("deploy.deploy_n8n_hetzner.time")
@patch("deploy.deploy_n8n_hetzner.get_ssh_client")
@patch("deploy.deploy_n8n_hetzner.VPS_HOST", "10.0.0.1")
@patch("deploy.deploy_n8n_hetzner.N8N_EMAIL", "admin@test.com")
@patch("deploy.deploy_n8n_hetzner.N8N_PASSWORD", "testpw")
def test_main_writes_docker_compose(mock_get_ssh, mock_time):
    """main() should write docker-compose.yml via SFTP."""
    from deploy.deploy_n8n_hetzner import main

    ssh = _mock_ssh(stdout="ok")
    mock_file = MagicMock()
    mock_file.__enter__ = MagicMock(return_value=mock_file)
    mock_file.__exit__ = MagicMock(return_value=False)
    sftp = MagicMock()
    sftp.open.return_value = mock_file
    ssh.open_sftp.return_value = sftp
    mock_get_ssh.return_value = ssh

    main()

    # SFTP should write docker-compose and nginx config
    sftp_calls = [c[0][0] for c in sftp.open.call_args_list]
    assert "/opt/n8n/docker-compose.yml" in sftp_calls
    assert "/etc/nginx/sites-available/n8n" in sftp_calls


@patch("deploy.deploy_n8n_hetzner.time")
@patch("deploy.deploy_n8n_hetzner.get_ssh_client")
@patch("deploy.deploy_n8n_hetzner.VPS_HOST", "10.0.0.1")
@patch("deploy.deploy_n8n_hetzner.N8N_EMAIL", "admin@test.com")
@patch("deploy.deploy_n8n_hetzner.N8N_PASSWORD", "testpw")
def test_main_runs_expected_commands(mock_get_ssh, mock_time):
    """main() should execute mkdir, docker compose, nginx commands."""
    from deploy.deploy_n8n_hetzner import main

    ssh = _mock_ssh(stdout="ok")
    mock_file = MagicMock()
    mock_file.__enter__ = MagicMock(return_value=mock_file)
    mock_file.__exit__ = MagicMock(return_value=False)
    sftp = MagicMock()
    sftp.open.return_value = mock_file
    ssh.open_sftp.return_value = sftp
    mock_get_ssh.return_value = ssh

    main()

    cmds = [c[0][0] for c in ssh.exec_command.call_args_list]
    # Should create directory
    assert any("mkdir" in c for c in cmds)
    # Should pull and start docker compose
    assert any("docker compose pull" in c for c in cmds)
    assert any("docker compose up -d" in c for c in cmds)
    # Should test and reload nginx
    assert any("nginx -t" in c for c in cmds)


@patch("deploy.deploy_n8n_hetzner.time")
@patch("deploy.deploy_n8n_hetzner.get_ssh_client")
@patch("deploy.deploy_n8n_hetzner.VPS_HOST", "10.0.0.1")
@patch("deploy.deploy_n8n_hetzner.N8N_EMAIL", "admin@test.com")
@patch("deploy.deploy_n8n_hetzner.N8N_PASSWORD", "testpw")
def test_main_closes_connections(mock_get_ssh, mock_time):
    """main() should close both SFTP and SSH connections."""
    from deploy.deploy_n8n_hetzner import main

    ssh = _mock_ssh(stdout="ok")
    mock_file = MagicMock()
    mock_file.__enter__ = MagicMock(return_value=mock_file)
    mock_file.__exit__ = MagicMock(return_value=False)
    sftp = MagicMock()
    sftp.open.return_value = mock_file
    ssh.open_sftp.return_value = sftp
    mock_get_ssh.return_value = ssh

    main()

    sftp.close.assert_called_once()
    ssh.close.assert_called_once()


@patch("deploy.deploy_n8n_hetzner.time")
@patch("deploy.deploy_n8n_hetzner.get_ssh_client")
@patch("deploy.deploy_n8n_hetzner.VPS_HOST", "10.0.0.1")
@patch("deploy.deploy_n8n_hetzner.N8N_EMAIL", "")
@patch("deploy.deploy_n8n_hetzner.N8N_PASSWORD", "testpw")
def test_main_defaults_user_to_admin(mock_get_ssh, mock_time):
    """When N8N_EMAIL is empty, docker compose should use 'admin'."""
    from deploy.deploy_n8n_hetzner import main

    ssh = _mock_ssh(stdout="ok")
    mock_file = MagicMock()
    mock_file.__enter__ = MagicMock(return_value=mock_file)
    mock_file.__exit__ = MagicMock(return_value=False)
    written = []
    mock_file.write = written.append
    sftp = MagicMock()
    sftp.open.return_value = mock_file
    ssh.open_sftp.return_value = sftp
    mock_get_ssh.return_value = ssh

    main()

    # First write should be docker-compose content
    docker_content = written[0]
    assert "N8N_BASIC_AUTH_USER=admin" in docker_content


@patch("deploy.deploy_n8n_hetzner.time")
@patch("deploy.deploy_n8n_hetzner.get_ssh_client")
@patch("deploy.deploy_n8n_hetzner.VPS_HOST", "10.0.0.1")
@patch("deploy.deploy_n8n_hetzner.N8N_EMAIL", "admin@test.com")
@patch("deploy.deploy_n8n_hetzner.N8N_PASSWORD", "testpw")
def test_main_masks_password_in_output(mock_get_ssh, mock_time, capsys):
    """main() should not print the actual password."""
    from deploy.deploy_n8n_hetzner import main

    ssh = _mock_ssh(stdout="ok")
    mock_file = MagicMock()
    mock_file.__enter__ = MagicMock(return_value=mock_file)
    mock_file.__exit__ = MagicMock(return_value=False)
    sftp = MagicMock()
    sftp.open.return_value = mock_file
    ssh.open_sftp.return_value = sftp
    mock_get_ssh.return_value = ssh

    main()

    captured = capsys.readouterr()
    assert "testpw" not in captured.out
    assert "***" in captured.out
