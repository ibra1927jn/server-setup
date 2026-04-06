"""Tests for monitoring/server_monitor.py — system checks, docker, alerting, formatting."""

import json
import subprocess
from unittest.mock import MagicMock, mock_open, patch

from monitoring.server_monitor import (
    CRITICAL,
    INFO,
    WARNING,
    CheckResult,
    MonitorReport,
    check_cpu,
    check_disk,
    check_docker,
    check_load,
    check_ram,
    check_swap,
    docker_check_results,
    format_telegram_message,
    run_checks,
    send_telegram,
    should_alert,
)

# ── _load_telegram_config ───────────────────────────────────

def test_load_telegram_config_import_error():
    """Lines 34-35: fallback to env vars when shared_config is unavailable."""
    from monitoring.server_monitor import _load_telegram_config

    with (
        patch.dict("sys.modules", {"shared_config": None}),
        patch.dict("os.environ", {"TELEGRAM_BOT_TOKEN": "env_tok", "TELEGRAM_CHAT_ID": "env_id"}),
    ):
        token, chat_id = _load_telegram_config()
    assert token == "env_tok"  # noqa: S105
    assert chat_id == "env_id"


# ── check_disk ──────────────────────────────────────────────

DF_HEADER = "Mounted on  Use% Size  Used Avail\n"


def test_check_disk_ok():
    df_out = DF_HEADER + "/            30%  50G  15G  35G\n"
    with patch("subprocess.check_output", return_value=df_out):
        results = check_disk()
    assert len(results) == 1
    assert results[0].severity == INFO
    assert results[0].name == "disk:/"


def test_check_disk_warning():
    df_out = DF_HEADER + "/            85%  50G  42G  8G\n"
    with patch("subprocess.check_output", return_value=df_out):
        results = check_disk()
    assert results[0].severity == WARNING


def test_check_disk_critical():
    df_out = DF_HEADER + "/            95%  50G  47G  3G\n"
    with patch("subprocess.check_output", return_value=df_out):
        results = check_disk()
    assert results[0].severity == CRITICAL


def test_check_disk_skips_pseudo_fs():
    df_out = DF_HEADER + "/dev         1%  1G   1M   1G\n"
    with patch("subprocess.check_output", return_value=df_out):
        results = check_disk()
    assert results[0].message == "No monitored filesystems found"


def test_check_disk_subprocess_error():
    with patch("subprocess.check_output", side_effect=subprocess.CalledProcessError(1, "df")):
        results = check_disk()
    assert results[0].severity == CRITICAL
    assert "Failed" in results[0].message


def test_check_disk_mnt_prefix():
    df_out = DF_HEADER + "/mnt/data    50%  100G  50G  50G\n"
    with patch("subprocess.check_output", return_value=df_out):
        results = check_disk()
    assert results[0].name == "disk:/mnt/data"


def test_check_disk_short_line_skipped():
    df_out = DF_HEADER + "short\n"
    with patch("subprocess.check_output", return_value=df_out):
        results = check_disk()
    assert results[0].message == "No monitored filesystems found"


def test_check_disk_skips_non_standard_mount():
    """Line 110: mounts not in the allowed list and not /mnt/* are skipped."""
    df_out = DF_HEADER + "/opt/custom  50%  100G  50G  50G\n"
    with patch("subprocess.check_output", return_value=df_out):
        results = check_disk()
    assert results[0].message == "No monitored filesystems found"


# ── check_ram ───────────────────────────────────────────────

_FREE_HDR = "              total    used    free  shared  buff   available\n"
_FREE_SWAP = "Swap:          2000     200    1800\n"
FREE_OK = _FREE_HDR + "Mem:          16000    4000    8000    100    2000    12000\n" + _FREE_SWAP
FREE_WARN = _FREE_HDR + "Mem:          16000   12000    2000    100    1000     3200\n" + _FREE_SWAP
FREE_CRIT = _FREE_HDR + "Mem:          16000   14000     500    100     500     1600\n" + _FREE_SWAP


def test_check_ram_ok():
    with patch("subprocess.check_output", return_value=FREE_OK):
        r = check_ram()
    assert r.severity == INFO


def test_check_ram_warning():
    with patch("subprocess.check_output", return_value=FREE_WARN):
        r = check_ram()
    assert r.severity == WARNING


def test_check_ram_critical():
    with patch("subprocess.check_output", return_value=FREE_CRIT):
        r = check_ram()
    assert r.severity == CRITICAL


def test_check_ram_error():
    with patch("subprocess.check_output", side_effect=subprocess.CalledProcessError(1, "free")):
        r = check_ram()
    assert r.severity == CRITICAL


def test_check_ram_no_mem_line():
    with patch("subprocess.check_output", return_value="header\nSwap: 0 0 0\n"):
        r = check_ram()
    assert "Could not parse" in r.message


# ── check_swap ──────────────────────────────────────────────

def test_check_swap_ok():
    with patch("subprocess.check_output", return_value=FREE_OK):
        r = check_swap()
    assert r.severity == INFO


def test_check_swap_no_swap():
    free_out = "header\nMem: 16000 4000 8000 100 2000 12000\nSwap:          0       0       0\n"
    with patch("subprocess.check_output", return_value=free_out):
        r = check_swap()
    assert r.severity == INFO
    assert "not configured" in r.message


def test_check_swap_warning():
    free_out = "header\nMem: 16000 4000 8000 100 2000 12000\nSwap:       2000    1200     800\n"
    with patch("subprocess.check_output", return_value=free_out):
        r = check_swap()
    assert r.severity == WARNING


def test_check_swap_critical():
    free_out = "header\nMem: 16000 4000 8000 100 2000 12000\nSwap:       2000    1800     200\n"
    with patch("subprocess.check_output", return_value=free_out):
        r = check_swap()
    assert r.severity == CRITICAL


def test_check_swap_error():
    with patch("subprocess.check_output", side_effect=subprocess.CalledProcessError(1, "free")):
        r = check_swap()
    assert r.severity == CRITICAL


def test_check_swap_no_swap_line():
    with patch("subprocess.check_output", return_value="header\nMem: 16000 4000 8000 100 2000 12000\n"):
        r = check_swap()
    assert "No swap" in r.message


# ── check_cpu ───────────────────────────────────────────────

def test_check_cpu_via_loadavg():
    with (
        patch("subprocess.check_output", side_effect=FileNotFoundError),
        patch("pathlib.Path.open", mock_open(read_data="0.50 0.40 0.30 1/200 12345")),
        patch("os.cpu_count", return_value=2),
    ):
        r = check_cpu()
    assert r.severity == INFO
    assert "CPU" in r.message


def test_check_cpu_via_mpstat():
    mpstat_out = "Linux 6.1\n\n12:00:00  CPU  %usr  %nice  %sys  %idle\n12:00:01  all  20.0  0.0  5.0  75.0\n"
    with patch("subprocess.check_output", return_value=mpstat_out):
        r = check_cpu()
    assert r.severity == INFO
    assert "25%" in r.value


def test_check_cpu_mpstat_high():
    mpstat_out = "Linux\n\n12:00:00  CPU  %idle\n12:00:01  all  2.0\n"
    with patch("subprocess.check_output", return_value=mpstat_out):
        r = check_cpu()
    assert r.severity == CRITICAL


def test_check_cpu_mpstat_warning():
    """Line 234: CPU usage between warning and critical thresholds."""
    mpstat_out = "Linux\n\n12:00:00  CPU  %idle\n12:00:01  all  15.0\n"
    with patch("subprocess.check_output", return_value=mpstat_out):
        r = check_cpu()
    assert r.severity == WARNING
    assert "85%" in r.value


def test_check_cpu_loadavg_fallback_error():
    with (
        patch("subprocess.check_output", side_effect=FileNotFoundError),
        patch("pathlib.Path.open", side_effect=OSError("no file")),
    ):
        r = check_cpu()
    assert r.severity == WARNING
    assert "Cannot read" in r.message


def test_check_cpu_mpstat_unparseable():
    mpstat_out = "Linux\n\nAverage:  all unparseable\n"
    with patch("subprocess.check_output", return_value=mpstat_out):
        r = check_cpu()
    assert "Could not parse" in r.message


# ── check_load ──────────────────────────────────────────────

def test_check_load_ok():
    with patch("os.getloadavg", return_value=(0.5, 0.4, 0.3)), patch("os.cpu_count", return_value=4):
        r = check_load()
    assert r.severity == INFO


def test_check_load_warning():
    with patch("os.getloadavg", return_value=(5.0, 5.0, 4.0)), patch("os.cpu_count", return_value=4):
        r = check_load()
    assert r.severity == WARNING


def test_check_load_critical():
    with patch("os.getloadavg", return_value=(20.0, 20.0, 18.0)), patch("os.cpu_count", return_value=4):
        r = check_load()
    assert r.severity == CRITICAL


def test_check_load_error():
    with patch("os.getloadavg", side_effect=OSError):
        r = check_load()
    assert r.severity == WARNING
    assert "Cannot read" in r.message


# ── check_docker ────────────────────────────────────────────

def test_check_docker_running():
    docker_out = "abc123\tn8n\tUp 2 hours (healthy)\tn8nio/n8n\n"
    with patch("subprocess.check_output", return_value=docker_out):
        containers = check_docker()
    assert len(containers) == 1
    assert containers[0]["health"] == "healthy"


def test_check_docker_unhealthy():
    docker_out = "abc123\tn8n\tUp 2 hours (unhealthy)\tn8nio/n8n\n"
    with patch("subprocess.check_output", return_value=docker_out):
        containers = check_docker()
    assert containers[0]["health"] == "unhealthy"


def test_check_docker_exited():
    docker_out = "abc123\tredis\tExited (0) 1 hour ago\tredis:7\n"
    with patch("subprocess.check_output", return_value=docker_out):
        containers = check_docker()
    assert containers[0]["health"] == "exited"


def test_check_docker_restarting():
    docker_out = "abc123\tapp\tRestarting (1) 5 seconds ago\tapp:latest\n"
    with patch("subprocess.check_output", return_value=docker_out):
        containers = check_docker()
    assert containers[0]["health"] == "restarting"


def test_check_docker_up_no_healthcheck():
    docker_out = "abc123\tapp\tUp 10 minutes\tapp:latest\n"
    with patch("subprocess.check_output", return_value=docker_out):
        containers = check_docker()
    assert containers[0]["health"] == "running"


def test_check_docker_error():
    with patch("subprocess.check_output", side_effect=FileNotFoundError):
        containers = check_docker()
    assert containers == []


def test_check_docker_empty_output():
    with patch("subprocess.check_output", return_value="\n"):
        containers = check_docker()
    assert containers == []


def test_check_docker_short_line():
    with patch("subprocess.check_output", return_value="abc\tname\n"):
        containers = check_docker()
    assert containers == []


# ── docker_check_results ────────────────────────────────────

def test_docker_check_results_empty():
    results = docker_check_results([])
    assert len(results) == 1
    assert results[0].severity == INFO


def test_docker_check_results_healthy():
    containers = [{"name": "n8n", "image": "n8nio/n8n", "status": "Up", "health": "healthy"}]
    results = docker_check_results(containers)
    assert results[0].severity == INFO


def test_docker_check_results_unhealthy():
    containers = [{"name": "n8n", "image": "n8nio/n8n", "status": "Up", "health": "unhealthy"}]
    results = docker_check_results(containers)
    assert results[0].severity == CRITICAL


def test_docker_check_results_exited():
    containers = [{"name": "redis", "image": "redis", "status": "Exited", "health": "exited"}]
    results = docker_check_results(containers)
    assert results[0].severity == WARNING


# ── format_telegram_message ─────────────────────────────────

def test_format_message_all_ok():
    report = MonitorReport(
        timestamp="2026-03-30 12:00:00",
        hostname="test-host",
        checks=[CheckResult("disk:/", "ok", "30%", "disk ok", INFO)],
        overall_severity=INFO,
    )
    msg = format_telegram_message(report)
    assert "All systems healthy" in msg
    assert "test-host" in msg


def test_format_message_with_warnings():
    report = MonitorReport(
        timestamp="2026-03-30 12:00:00",
        hostname="test-host",
        checks=[
            CheckResult("disk:/", "warning", "85%", "disk 85%", WARNING),
            CheckResult("ram", "ok", "30%", "ram ok", INFO),
        ],
        overall_severity=WARNING,
    )
    msg = format_telegram_message(report)
    assert "WARNING" in msg
    assert "1 checks OK" in msg


def test_format_message_with_criticals():
    report = MonitorReport(
        timestamp="2026-03-30",
        hostname="h",
        checks=[CheckResult("disk:/", "critical", "95%", "disk full", CRITICAL)],
        overall_severity=CRITICAL,
    )
    msg = format_telegram_message(report)
    assert "CRITICAL" in msg


def test_format_message_with_docker():
    report = MonitorReport(
        timestamp="2026-03-30",
        hostname="h",
        checks=[CheckResult("ok", "ok", "ok", "ok", INFO)],
        overall_severity=INFO,
        docker_containers=[
            {"name": "n8n", "health": "running"},
            {"name": "redis", "health": "exited"},
        ],
    )
    msg = format_telegram_message(report)
    assert "Docker" in msg
    assert "1/2 running" in msg
    assert "redis: exited" in msg


# ── send_telegram ───────────────────────────────────────────

def test_send_telegram_no_creds():
    result = send_telegram("test", token="", chat_id="")
    assert result is False


def test_send_telegram_success():
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.__enter__ = MagicMock(return_value=mock_resp)
    mock_resp.__exit__ = MagicMock(return_value=False)
    with patch("urllib.request.urlopen", return_value=mock_resp):
        result = send_telegram("test", token="tok", chat_id="123")
    assert result is True


def test_send_telegram_failure():
    import urllib.error

    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("fail")):
        result = send_telegram("test", token="tok", chat_id="123")
    assert result is False


def test_send_telegram_truncates_long_message():
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.__enter__ = MagicMock(return_value=mock_resp)
    mock_resp.__exit__ = MagicMock(return_value=False)
    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
        send_telegram("x" * 5000, token="tok", chat_id="123")
    # The request was made (message was truncated, not rejected)
    mock_urlopen.assert_called_once()


# ── should_alert ────────────────────────────────────────────

def test_should_alert_info_returns_false():
    report = MonitorReport(overall_severity=INFO)
    assert should_alert(report) is False


def test_should_alert_critical_returns_true():
    report = MonitorReport(overall_severity=CRITICAL)
    with patch("pathlib.Path.exists", return_value=False), patch("pathlib.Path.mkdir"), patch("pathlib.Path.open", mock_open()):
        assert should_alert(report) is True


def test_should_alert_warning_cooldown():
    state = json.dumps({"timestamp": 9999999999, "severity": WARNING})
    report = MonitorReport(overall_severity=WARNING)
    with (
        patch("pathlib.Path.exists", return_value=True),
        patch("pathlib.Path.open", mock_open(read_data=state)),
        patch("time.time", return_value=9999999999 + 60),
        patch("pathlib.Path.mkdir"),
    ):
        assert should_alert(report) is False


def test_should_alert_warning_after_cooldown():
    state = json.dumps({"timestamp": 1000, "severity": WARNING})
    report = MonitorReport(overall_severity=WARNING)
    with (
        patch("pathlib.Path.exists", return_value=True),
        patch("pathlib.Path.open", mock_open(read_data=state)),
        patch("time.time", return_value=2000),
        patch("pathlib.Path.mkdir"),
    ):
        assert should_alert(report) is True


def test_should_alert_state_file_error():
    report = MonitorReport(overall_severity=CRITICAL)
    with (
        patch("pathlib.Path.exists", side_effect=OSError),
        patch("pathlib.Path.mkdir", side_effect=OSError),
    ):
        assert should_alert(report) is True


# ── run_checks ──────────────────────────────────────────────

def test_run_checks_returns_report():
    with (
        patch("monitoring.server_monitor.check_disk", return_value=[CheckResult("disk:/", "ok", "30%", "ok", INFO)]),
        patch("monitoring.server_monitor.check_ram", return_value=CheckResult("ram", "ok", "30%", "ok", INFO)),
        patch("monitoring.server_monitor.check_swap", return_value=CheckResult("swap", "ok", "0%", "ok", INFO)),
        patch("monitoring.server_monitor.check_cpu", return_value=CheckResult("cpu", "ok", "10%", "ok", INFO)),
        patch("monitoring.server_monitor.check_load", return_value=CheckResult("load", "ok", "0.5", "ok", INFO)),
        patch("monitoring.server_monitor.check_docker", return_value=[]),
    ):
        report = run_checks()
    assert report.overall_severity == INFO
    assert len(report.checks) >= 5


def test_run_checks_critical_severity():
    with (
        patch("monitoring.server_monitor.check_disk", return_value=[CheckResult("disk:/", "critical", "95%", "full", CRITICAL)]),
        patch("monitoring.server_monitor.check_ram", return_value=CheckResult("ram", "ok", "30%", "ok", INFO)),
        patch("monitoring.server_monitor.check_swap", return_value=CheckResult("swap", "ok", "0%", "ok", INFO)),
        patch("monitoring.server_monitor.check_cpu", return_value=CheckResult("cpu", "ok", "10%", "ok", INFO)),
        patch("monitoring.server_monitor.check_load", return_value=CheckResult("load", "ok", "0.5", "ok", INFO)),
        patch("monitoring.server_monitor.check_docker", return_value=[]),
    ):
        report = run_checks()
    assert report.overall_severity == CRITICAL


def test_run_checks_warning_severity():
    """Line 484: overall severity is WARNING when no CRITICAL but has WARNING."""
    with (
        patch("monitoring.server_monitor.check_disk", return_value=[CheckResult("disk:/", "warning", "85%", "disk 85%", WARNING)]),
        patch("monitoring.server_monitor.check_ram", return_value=CheckResult("ram", "ok", "30%", "ok", INFO)),
        patch("monitoring.server_monitor.check_swap", return_value=CheckResult("swap", "ok", "0%", "ok", INFO)),
        patch("monitoring.server_monitor.check_cpu", return_value=CheckResult("cpu", "ok", "10%", "ok", INFO)),
        patch("monitoring.server_monitor.check_load", return_value=CheckResult("load", "ok", "0.5", "ok", INFO)),
        patch("monitoring.server_monitor.check_docker", return_value=[]),
    ):
        report = run_checks()
    assert report.overall_severity == WARNING


# ── main ────────────────────────────────────────────────────

def test_main_json(capsys):
    from monitoring.server_monitor import main

    mock_report = MonitorReport(
        timestamp="2026-03-30",
        hostname="test",
        checks=[CheckResult("disk:/", "ok", "30%", "ok", INFO)],
        overall_severity=INFO,
    )
    with (
        patch("monitoring.server_monitor.run_checks", return_value=mock_report),
        patch("sys.argv", ["server_monitor.py", "--json"]),
    ):
        main()
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["overall_severity"] == "info"


def test_main_dry_run(capsys):
    from monitoring.server_monitor import main

    mock_report = MonitorReport(
        timestamp="2026-03-30",
        hostname="test",
        checks=[CheckResult("disk:/", "ok", "30%", "ok", INFO)],
        overall_severity=INFO,
    )
    with (
        patch("monitoring.server_monitor.run_checks", return_value=mock_report),
        patch("sys.argv", ["server_monitor.py", "--dry-run"]),
    ):
        main()
    out = capsys.readouterr().out
    assert "dry-run" in out


def test_main_force_alert(capsys):
    from monitoring.server_monitor import main

    mock_report = MonitorReport(
        timestamp="2026-03-30",
        hostname="test",
        checks=[CheckResult("disk:/", "ok", "30%", "ok", INFO)],
        overall_severity=INFO,
    )
    with (
        patch("monitoring.server_monitor.run_checks", return_value=mock_report),
        patch("monitoring.server_monitor.send_telegram", return_value=True) as mock_send,
        patch("monitoring.server_monitor.should_alert", return_value=False),
        patch("sys.argv", ["server_monitor.py", "--force-alert"]),
    ):
        main()
    mock_send.assert_called_once()
    out = capsys.readouterr().out
    assert "sent" in out


def test_main_info_alert(capsys):
    """--info-alert sends alert even for INFO severity."""
    from monitoring.server_monitor import main

    mock_report = MonitorReport(
        timestamp="2026-03-30",
        hostname="test",
        checks=[CheckResult("disk:/", "ok", "30%", "ok", INFO)],
        overall_severity=INFO,
    )
    with (
        patch("monitoring.server_monitor.run_checks", return_value=mock_report),
        patch("monitoring.server_monitor.send_telegram", return_value=True) as mock_send,
        patch("monitoring.server_monitor.should_alert", return_value=False),
        patch("sys.argv", ["server_monitor.py", "--info-alert"]),
    ):
        main()
    mock_send.assert_called_once()
    out = capsys.readouterr().out
    assert "sent" in out


def test_main_no_alert(capsys):
    from monitoring.server_monitor import main

    mock_report = MonitorReport(
        timestamp="2026-03-30",
        hostname="test",
        checks=[CheckResult("disk:/", "ok", "30%", "ok", INFO)],
        overall_severity=INFO,
    )
    with (
        patch("monitoring.server_monitor.run_checks", return_value=mock_report),
        patch("monitoring.server_monitor.should_alert", return_value=False),
        patch("sys.argv", ["server_monitor.py"]),
    ):
        main()
    out = capsys.readouterr().out
    assert "No alert needed" in out
