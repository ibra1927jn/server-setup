"""Deploy n8n to Hetzner VPS via Docker"""
from shared_config import get_ssh_client, VPS_HOST

def run(ssh, cmd, label=""):
    if label:
        print(f"\n=== {label} ===")
    print(f"$ {cmd[:80]}")
    _, o, e = ssh.exec_command(cmd, timeout=120)
    out = o.read().decode().strip()
    err = e.read().decode().strip()
    if out:
        print(out)
    if err:
        print(f"[stderr] {err}")
    return out

def main():
    print(f"Connecting to {VPS_HOST}...")
    ssh = get_ssh_client()

    # Check server resources
    run(ssh, "df -h / | tail -1", "DISK")
    run(ssh, "free -h | head -2", "RAM")
    run(ssh, "docker --version 2>/dev/null || echo 'NO_DOCKER'", "DOCKER")
    run(ssh, "docker compose version 2>/dev/null || docker-compose --version 2>/dev/null || echo 'NO_COMPOSE'", "COMPOSE")
    run(ssh, "nginx -v 2>&1 || echo 'NO_NGINX'", "NGINX")
    run(ssh, "ss -tlnp | grep -E ':(80|443|5678) ' || echo 'Ports 80/443/5678 free'", "PORTS")

    ssh.close()
    print("\n=== DONE ===")

if __name__ == "__main__":
    main()
