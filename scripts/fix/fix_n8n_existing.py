"""Stop old ultra_n8n and restart with fixed config"""
import time

from shared_config import get_ssh_client


def main():
    ssh = get_ssh_client()

    def run(cmd, label=""):
        if label:
            print(f"\n=== {label} ===")
        _, o, e = ssh.exec_command(cmd, timeout=60)
        out = o.read().decode().strip()
        err = e.read().decode().strip()
        if out:
            print(out)
        if err and 'warn' not in err.lower():
            print(f"[err] {err}")
        return out

    # Stop ALL n8n containers
    run(
        "docker stop ultra_n8n 2>/dev/null;"
        " docker rm ultra_n8n 2>/dev/null",
        "Stop ultra_n8n",
    )
    run(
        "docker stop n8n 2>/dev/null;"
        " docker rm n8n 2>/dev/null",
        "Stop n8n",
    )
    run(
        "docker stop n8n-n8n-1 2>/dev/null;"
        " docker rm n8n-n8n-1 2>/dev/null",
        "Stop n8n-n8n-1",
    )

    # Check port is free
    run("ss -tlnp | grep 5678 || echo 'Port 5678 is FREE'", "Port check")

    # Clean up /opt/n8n
    run("cd /opt/n8n && docker compose down 2>&1; rm -rf /opt/n8n", "Clean /opt/n8n")

    # Start from /root/n8n with the correct compose
    run("cd /root/n8n && docker compose up -d 2>&1", "Start n8n")

    print("\nWaiting 20s...")
    time.sleep(20)

    # Verify
    run(
        "docker ps --format 'table {{.Names}}\t{{.Status}}"
        "\t{{.Ports}}' | grep -i n8n",
        "Final status",
    )
    code = run(
        "curl -s -o /dev/null -w '%{http_code}'"
        " http://localhost:5678/setup",
        "Setup page",
    )
    run("curl -s http://localhost:5678/healthz", "Health")

    ssh.close()
    print(f"\n=== DONE === Setup page: {code}")


if __name__ == "__main__":
    main()
