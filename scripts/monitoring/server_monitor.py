#!/usr/bin/env python3
"""
server_monitor.py — Centralized server monitoring with Telegram alerts.

Extends the existing heartbeat system with:
- Disk, RAM, CPU alerts with configurable thresholds
- Docker container health checks (aggregated view)
- Severity-level Telegram reporting (info, warning, critical)

Usage:
    python3 scripts/monitoring/server_monitor.py           # Run all checks
    python3 scripts/monitoring/server_monitor.py --dry-run  # Check without sending alerts
    python3 scripts/monitoring/server_monitor.py --json     # Output JSON report

Designed to be called from cron or the existing heartbeat system.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

# Add parent dir so shared_config is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

def _load_telegram_config():
    """Load Telegram config from shared_config or environment."""
    try:
        from shared_config import TELEGRAM_BOT_TOKEN as _token, TELEGRAM_CHAT_ID as _chat
        return _token, _chat
    except ImportError:
        return os.getenv("TELEGRAM_BOT_TOKEN", ""), os.getenv("TELEGRAM_CHAT_ID", "")

_TG_TOKEN, _TG_CHAT = _load_telegram_config()

# ── Configurable thresholds (env overrides) ──────────────────

THRESHOLDS = {
    "disk_warning_pct": int(os.getenv("MON_DISK_WARN", "80")),
    "disk_critical_pct": int(os.getenv("MON_DISK_CRIT", "90")),
    "ram_warning_pct": int(os.getenv("MON_RAM_WARN", "80")),
    "ram_critical_pct": int(os.getenv("MON_RAM_CRIT", "90")),
    "cpu_warning_pct": int(os.getenv("MON_CPU_WARN", "80")),
    "cpu_critical_pct": int(os.getenv("MON_CPU_CRIT", "95")),
    "swap_warning_pct": int(os.getenv("MON_SWAP_WARN", "50")),
    "swap_critical_pct": int(os.getenv("MON_SWAP_CRIT", "80")),
}

# Severity levels
INFO = "info"
WARNING = "warning"
CRITICAL = "critical"

SEVERITY_EMOJI = {
    INFO: "\u2705",       # green check
    WARNING: "\u26a0\ufe0f",  # warning sign
    CRITICAL: "\U0001f534",   # red circle
}

STATE_DIR = Path(os.getenv("MON_STATE_DIR", "/opt/heartbeat/state"))
LOG_DIR = Path(os.getenv("MON_LOG_DIR", "/opt/heartbeat/logs"))


@dataclass
class CheckResult:
    name: str
    status: str  # ok, warning, critical
    value: str
    message: str
    severity: str = INFO


@dataclass
class MonitorReport:
    timestamp: str = ""
    hostname: str = ""
    checks: list = field(default_factory=list)
    overall_severity: str = INFO
    docker_containers: list = field(default_factory=list)


# ── System checks ────────────────────────────────────────────

def check_disk() -> list[CheckResult]:
    """Check disk usage for all mounted filesystems."""
    results = []
    try:
        output = subprocess.check_output(
            ["df", "-h", "--output=target,pcent,size,used,avail"],
            text=True,
        )
    except subprocess.CalledProcessError:
        return [CheckResult("disk", CRITICAL, "N/A", "Failed to run df")]

    for line in output.strip().split("\n")[1:]:
        parts = line.split()
        if len(parts) < 5:
            continue
        mount, pct_str = parts[0], parts[1]
        # Skip pseudo-filesystems
        if mount.startswith(("/dev", "/sys", "/proc", "/run", "/snap")):
            continue
        # Only check real mounts
        if mount not in ("/", "/home", "/mnt", "/var", "/tmp") and not mount.startswith("/mnt/"):
            continue

        pct = int(pct_str.rstrip("%"))
        size, used, avail = parts[2], parts[3], parts[4]

        if pct >= THRESHOLDS["disk_critical_pct"]:
            severity = CRITICAL
        elif pct >= THRESHOLDS["disk_warning_pct"]:
            severity = WARNING
        else:
            severity = INFO

        results.append(CheckResult(
            name=f"disk:{mount}",
            status="critical" if severity == CRITICAL else "warning" if severity == WARNING else "ok",
            value=f"{pct}%",
            message=f"{mount}: {used}/{size} ({pct}%), {avail} free",
            severity=severity,
        ))

    return results or [CheckResult("disk", INFO, "N/A", "No monitored filesystems found")]


def check_ram() -> CheckResult:
    """Check RAM usage."""
    try:
        output = subprocess.check_output(["free", "-m"], text=True)
    except subprocess.CalledProcessError:
        return CheckResult("ram", CRITICAL, "N/A", "Failed to run free")

    for line in output.strip().split("\n"):
        if line.startswith("Mem:"):
            parts = line.split()
            total = int(parts[1])
            available = int(parts[6])  # 'available' column
            used = total - available
            pct = round(used / total * 100) if total > 0 else 0

            if pct >= THRESHOLDS["ram_critical_pct"]:
                severity = CRITICAL
            elif pct >= THRESHOLDS["ram_warning_pct"]:
                severity = WARNING
            else:
                severity = INFO

            return CheckResult(
                name="ram",
                status="critical" if severity == CRITICAL else "warning" if severity == WARNING else "ok",
                value=f"{pct}%",
                message=f"RAM: {used}MB / {total}MB ({pct}%), {available}MB available",
                severity=severity,
            )

    return CheckResult("ram", CRITICAL, "N/A", "Could not parse free output")


def check_swap() -> CheckResult:
    """Check swap usage."""
    try:
        output = subprocess.check_output(["free", "-m"], text=True)
    except subprocess.CalledProcessError:
        return CheckResult("swap", CRITICAL, "N/A", "Failed to run free")

    for line in output.strip().split("\n"):
        if line.startswith("Swap:"):
            parts = line.split()
            total = int(parts[1])
            used = int(parts[2])
            if total == 0:
                return CheckResult("swap", INFO, "0%", "Swap: not configured", severity=INFO)
            pct = round(used / total * 100)

            if pct >= THRESHOLDS["swap_critical_pct"]:
                severity = CRITICAL
            elif pct >= THRESHOLDS["swap_warning_pct"]:
                severity = WARNING
            else:
                severity = INFO

            return CheckResult(
                name="swap",
                status="critical" if severity == CRITICAL else "warning" if severity == WARNING else "ok",
                value=f"{pct}%",
                message=f"Swap: {used}MB / {total}MB ({pct}%)",
                severity=severity,
            )

    return CheckResult("swap", INFO, "N/A", "No swap line found")


def check_cpu() -> CheckResult:
    """Check CPU usage via mpstat (1-second sample)."""
    try:
        output = subprocess.check_output(
            ["mpstat", "1", "1"],
            text=True,
            timeout=10,
        )
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        # Fallback: use /proc/loadavg
        try:
            with open("/proc/loadavg") as f:
                load = float(f.read().split()[0])
            ncpu = os.cpu_count() or 1
            pct = round(load / ncpu * 100)
            pct = min(pct, 100)
        except (OSError, ValueError):
            return CheckResult("cpu", WARNING, "N/A", "Cannot read CPU stats")
    else:
        # Parse mpstat output: last line, last column is %idle
        for line in reversed(output.strip().split("\n")):
            parts = line.split()
            if parts and parts[0] != "Average:":
                try:
                    idle = float(parts[-1])
                    pct = round(100 - idle)
                    break
                except (ValueError, IndexError):
                    continue
        else:
            return CheckResult("cpu", WARNING, "N/A", "Could not parse mpstat output")

    if pct >= THRESHOLDS["cpu_critical_pct"]:
        severity = CRITICAL
    elif pct >= THRESHOLDS["cpu_warning_pct"]:
        severity = WARNING
    else:
        severity = INFO

    return CheckResult(
        name="cpu",
        status="critical" if severity == CRITICAL else "warning" if severity == WARNING else "ok",
        value=f"{pct}%",
        message=f"CPU: {pct}% utilized",
        severity=severity,
    )


def check_load() -> CheckResult:
    """Check system load average."""
    try:
        load1, load5, load15 = os.getloadavg()
    except OSError:
        return CheckResult("load", WARNING, "N/A", "Cannot read load average")

    ncpu = os.cpu_count() or 1
    ratio = load5 / ncpu

    if ratio > 2.0:
        severity = CRITICAL
    elif ratio > 1.0:
        severity = WARNING
    else:
        severity = INFO

    return CheckResult(
        name="load",
        status="critical" if severity == CRITICAL else "warning" if severity == WARNING else "ok",
        value=f"{load5:.2f}",
        message=f"Load avg: {load1:.2f} / {load5:.2f} / {load15:.2f} ({ncpu} CPUs, ratio={ratio:.2f})",
        severity=severity,
    )


# ── Docker checks ────────────────────────────────────────────

def check_docker() -> list[dict]:
    """Check Docker container health. Returns list of container status dicts."""
    containers = []
    try:
        output = subprocess.check_output(
            ["docker", "ps", "-a", "--format", "{{.ID}}\t{{.Names}}\t{{.Status}}\t{{.Image}}"],
            text=True,
            timeout=10,
        )
    except (subprocess.CalledProcessError, FileNotFoundError, PermissionError, subprocess.TimeoutExpired):
        return []

    for line in output.strip().split("\n"):
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) < 4:
            continue
        cid, name, status, image = parts[0], parts[1], parts[2], parts[3]

        health = "unknown"
        if "Up" in status:
            if "(healthy)" in status:
                health = "healthy"
            elif "(unhealthy)" in status:
                health = "unhealthy"
            else:
                health = "running"
        elif "Exited" in status:
            health = "exited"
        elif "Restarting" in status:
            health = "restarting"

        containers.append({
            "id": cid,
            "name": name,
            "image": image,
            "status": status,
            "health": health,
        })

    return containers


def docker_check_results(containers: list[dict]) -> list[CheckResult]:
    """Convert docker container list to CheckResults."""
    if not containers:
        return [CheckResult(
            "docker", INFO, "N/A",
            "Docker: no containers found or no access",
            severity=INFO,
        )]

    results = []
    for c in containers:
        if c["health"] in ("unhealthy", "restarting"):
            severity = CRITICAL
        elif c["health"] == "exited":
            severity = WARNING
        else:
            severity = INFO

        results.append(CheckResult(
            name=f"docker:{c['name']}",
            status=c["health"],
            value=c["health"],
            message=f"{c['name']} ({c['image']}): {c['status']}",
            severity=severity,
        ))

    return results


# ── Telegram alerting ────────────────────────────────────────

def send_telegram(message: str, token: str = "", chat_id: str = "") -> bool:
    """Send a Telegram message. Returns True on success."""
    token = token or _TG_TOKEN
    chat_id = chat_id or _TG_CHAT

    if not token or not chat_id:
        print("[monitor] Telegram credentials not configured, skipping alert", file=sys.stderr)
        return False

    import urllib.request
    import urllib.parse

    # Truncate to Telegram limit
    if len(message) > 4000:
        message = message[:3990] + "\n..."

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": "true",
    }).encode()

    try:
        req = urllib.request.Request(url, data=data, method="POST")
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception as e:
        print(f"[monitor] Telegram send failed: {e}", file=sys.stderr)
        return False


def format_telegram_message(report: MonitorReport) -> str:
    """Format the monitoring report as a Telegram message."""
    emoji = SEVERITY_EMOJI.get(report.overall_severity, "\u2753")
    header = f"{emoji} *Server Monitor — {report.hostname}*"

    # Group checks by severity
    criticals = [c for c in report.checks if c.severity == CRITICAL]
    warnings = [c for c in report.checks if c.severity == WARNING]
    ok_checks = [c for c in report.checks if c.severity == INFO]

    lines = [header, ""]

    if criticals:
        lines.append("\U0001f534 *CRITICAL:*")
        for c in criticals:
            lines.append(f"  \u2022 {c.message}")
        lines.append("")

    if warnings:
        lines.append("\u26a0\ufe0f *WARNING:*")
        for c in warnings:
            lines.append(f"  \u2022 {c.message}")
        lines.append("")

    # Only show OK summary in info-level reports (no problems)
    if not criticals and not warnings:
        lines.append("\u2705 All systems healthy")
        lines.append(f"  \u2022 {len(ok_checks)} checks passed")
    else:
        lines.append(f"\u2705 {len(ok_checks)} checks OK")

    # Docker container summary
    if report.docker_containers:
        running = sum(1 for c in report.docker_containers if c["health"] in ("running", "healthy"))
        total = len(report.docker_containers)
        problem = [c for c in report.docker_containers if c["health"] in ("unhealthy", "restarting", "exited")]
        lines.append("")
        lines.append(f"\U0001f433 *Docker:* {running}/{total} running")
        for c in problem:
            lines.append(f"  \u2022 {c['name']}: {c['health']}")

    lines.append(f"\n_{report.timestamp}_")
    return "\n".join(lines)


def should_alert(report: MonitorReport) -> bool:
    """Decide whether to send a Telegram alert based on severity and cooldown."""
    if report.overall_severity == INFO:
        return False  # Don't alert on all-OK

    # Cooldown: don't spam alerts within 15 minutes for warnings
    state_file = STATE_DIR / "monitor-last-alert.json"
    now = time.time()

    try:
        if state_file.exists():
            with open(state_file) as f:
                state = json.load(f)
            last_time = state.get("timestamp", 0)
            last_severity = state.get("severity", INFO)

            # Critical always alerts; warning has 15-min cooldown
            if report.overall_severity == WARNING and last_severity != CRITICAL:
                if now - last_time < 900:
                    return False
    except (json.JSONDecodeError, OSError):
        pass

    # Save state
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        with open(state_file, "w") as f:
            json.dump({"timestamp": now, "severity": report.overall_severity}, f)
    except OSError:
        pass  # State dir may not be writable

    return True


# ── Main ─────────────────────────────────────────────────────

def run_checks() -> MonitorReport:
    """Run all monitoring checks and return a report."""
    report = MonitorReport(
        timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
        hostname=os.uname().nodename,
    )

    # System checks
    report.checks.extend(check_disk())
    report.checks.append(check_ram())
    report.checks.append(check_swap())
    report.checks.append(check_cpu())
    report.checks.append(check_load())

    # Docker checks
    report.docker_containers = check_docker()
    report.checks.extend(docker_check_results(report.docker_containers))

    # Determine overall severity
    severities = [c.severity for c in report.checks]
    if CRITICAL in severities:
        report.overall_severity = CRITICAL
    elif WARNING in severities:
        report.overall_severity = WARNING
    else:
        report.overall_severity = INFO

    return report


def main():
    parser = argparse.ArgumentParser(description="Server monitoring with Telegram alerts")
    parser.add_argument("--dry-run", action="store_true", help="Run checks without sending alerts")
    parser.add_argument("--json", action="store_true", help="Output JSON report")
    parser.add_argument("--force-alert", action="store_true", help="Send alert regardless of severity/cooldown")
    parser.add_argument("--info-alert", action="store_true", help="Also send alerts for info (all-OK) status")
    args = parser.parse_args()

    report = run_checks()

    if args.json:
        output = {
            "timestamp": report.timestamp,
            "hostname": report.hostname,
            "overall_severity": report.overall_severity,
            "checks": [asdict(c) for c in report.checks],
            "docker_containers": report.docker_containers,
            "thresholds": THRESHOLDS,
        }
        print(json.dumps(output, indent=2))
        return

    # Print human-readable summary
    msg = format_telegram_message(report)
    print(msg)

    if args.dry_run:
        print("\n[dry-run] Alert not sent")
        return

    # Decide whether to alert
    do_alert = args.force_alert or args.info_alert or should_alert(report)
    if args.info_alert and report.overall_severity == INFO:
        do_alert = True

    if do_alert:
        success = send_telegram(msg)
        status = "sent" if success else "failed"
        print(f"\n[monitor] Telegram alert {status} (severity={report.overall_severity})")
    else:
        print(f"\n[monitor] No alert needed (severity={report.overall_severity})")


if __name__ == "__main__":
    main()
