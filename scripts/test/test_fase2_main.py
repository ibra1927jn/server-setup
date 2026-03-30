"""Tests for fase2_deploy.py main() with mocked SSH."""
import json
from unittest.mock import MagicMock, mock_open, patch


def _mock_ssh(stdout="", stderr=""):
    """Create a mock SSH client that returns given stdout/stderr."""
    ssh = MagicMock()
    o = MagicMock()
    o.read.return_value = stdout.encode()
    e = MagicMock()
    e.read.return_value = stderr.encode()
    ssh.exec_command.return_value = (MagicMock(), o, e)
    sftp = MagicMock()
    ssh.open_sftp.return_value = sftp
    return ssh


@patch("builtins.open", mock_open())
@patch("deploy.fase2_deploy.time")
@patch("deploy.fase2_deploy.get_ssh_client")
def test_main_runs_firewall_commands(mock_get_ssh, mock_time):
    """main() should execute firewall setup commands."""
    ssh = _mock_ssh()
    mock_get_ssh.return_value = ssh

    from deploy.fase2_deploy import main
    main()

    commands = [c[0][0] for c in ssh.exec_command.call_args_list]
    assert any("ufw default deny incoming" in cmd for cmd in commands)
    assert any("ufw allow 22/tcp" in cmd for cmd in commands)
    assert any("ufw enable" in cmd for cmd in commands)


@patch("builtins.open", mock_open())
@patch("deploy.fase2_deploy.time")
@patch("deploy.fase2_deploy.get_ssh_client")
def test_main_uploads_4_workflows_via_sftp(mock_get_ssh, mock_time):
    """main() should upload 4 workflow files via SFTP put."""
    ssh = _mock_ssh()
    sftp = ssh.open_sftp.return_value
    mock_get_ssh.return_value = ssh

    from deploy.fase2_deploy import main
    main()

    ssh.open_sftp.assert_called_once()
    assert sftp.put.call_count == 4
    for c in sftp.put.call_args_list:
        remote_path = c[0][1]
        assert remote_path.startswith("/tmp/n8n-import/")
        assert remote_path.endswith(".json")


@patch("builtins.open", mock_open())
@patch("deploy.fase2_deploy.time")
@patch("deploy.fase2_deploy.get_ssh_client")
def test_main_imports_workflows_into_n8n(mock_get_ssh, mock_time):
    """main() should docker cp and import each workflow."""
    ssh = _mock_ssh()
    mock_get_ssh.return_value = ssh

    from deploy.fase2_deploy import main
    main()

    commands = [c[0][0] for c in ssh.exec_command.call_args_list]
    import_cmds = [c for c in commands if "n8n import:workflow" in c]
    assert len(import_cmds) == 4


@patch("builtins.open", mock_open())
@patch("deploy.fase2_deploy.time")
@patch("deploy.fase2_deploy.get_ssh_client")
def test_main_activates_and_restarts(mock_get_ssh, mock_time):
    """main() should activate all workflows and restart n8n."""
    ssh = _mock_ssh()
    mock_get_ssh.return_value = ssh

    from deploy.fase2_deploy import main
    main()

    commands = [c[0][0] for c in ssh.exec_command.call_args_list]
    assert any("update:workflow --all --active=true" in cmd for cmd in commands)
    assert any("docker restart n8n-n8n-1" in cmd for cmd in commands)


@patch("builtins.open", mock_open())
@patch("deploy.fase2_deploy.time")
@patch("deploy.fase2_deploy.get_ssh_client")
def test_main_closes_connections(mock_get_ssh, mock_time):
    """main() should close both SFTP and SSH."""
    ssh = _mock_ssh()
    sftp = ssh.open_sftp.return_value
    mock_get_ssh.return_value = ssh

    from deploy.fase2_deploy import main
    main()

    sftp.close.assert_called_once()
    ssh.close.assert_called_once()


@patch("deploy.fase2_deploy.time")
@patch("deploy.fase2_deploy.get_ssh_client")
def test_main_writes_valid_workflow_json(mock_get_ssh, mock_time):
    """Workflow JSON written to local files should be valid with required fields."""
    ssh = _mock_ssh()
    mock_get_ssh.return_value = ssh

    written_data = {}

    def capturing_open(path, *args, **kwargs):
        if isinstance(path, str) and path.endswith(".json"):
            from io import StringIO
            buf = StringIO()
            buf.name = path
            buf.__enter__ = lambda s: s
            buf.__exit__ = lambda s, *a: None
            original_close = buf.close
            def capturing_close():
                written_data[path] = buf.getvalue()
                original_close()
            buf.close = capturing_close
            return buf
        return MagicMock()

    with patch("builtins.open", side_effect=capturing_open):
        from deploy.fase2_deploy import main
        main()

    assert len(written_data) == 4
    for data in written_data.values():
        wf = json.loads(data)
        assert "name" in wf
        assert "nodes" in wf
        assert "connections" in wf
        assert len(wf["nodes"]) >= 2


@patch("builtins.open", mock_open())
@patch("deploy.fase2_deploy.time")
@patch("deploy.fase2_deploy.get_ssh_client")
def test_main_docker_cp_each_workflow(mock_get_ssh, mock_time):
    """main() should docker cp each workflow file into the n8n container."""
    ssh = _mock_ssh()
    mock_get_ssh.return_value = ssh

    from deploy.fase2_deploy import main
    main()

    commands = [c[0][0] for c in ssh.exec_command.call_args_list]
    docker_cp_cmds = [c for c in commands if "docker cp" in c and "n8n-n8n-1" in c]
    assert len(docker_cp_cmds) == 4


@patch("builtins.open", mock_open())
@patch("deploy.fase2_deploy.time")
@patch("deploy.fase2_deploy.get_ssh_client")
def test_main_prints_firewall_stdout(mock_get_ssh, mock_time, capsys):
    """main() prints stdout from firewall commands when non-empty."""
    ssh = _mock_ssh(stdout="Rules updated")
    mock_get_ssh.return_value = ssh

    from deploy.fase2_deploy import main
    main()

    captured = capsys.readouterr()
    assert "Rules updated" in captured.out


@patch("builtins.open", mock_open())
@patch("deploy.fase2_deploy.time")
@patch("deploy.fase2_deploy.get_ssh_client")
def test_main_prints_firewall_and_import_errors(mock_get_ssh, mock_time, capsys):
    """main() prints ERR when stderr has errors (non-WARNING firewall, import error)."""
    ssh = _mock_ssh(stderr="error: something failed")
    mock_get_ssh.return_value = ssh

    from deploy.fase2_deploy import main
    main()

    captured = capsys.readouterr()
    assert "ERR: error: something failed" in captured.out
