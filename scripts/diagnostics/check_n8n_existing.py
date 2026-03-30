"""Investigate existing n8n on Hetzner and fix secure cookie"""
from shared_config import get_ssh_client

ssh = get_ssh_client()

cmds = [
    ("All docker containers", "docker ps -a --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}\t{{.Image}}'"),
    (
        "ultra_n8n env vars",
        "docker inspect ultra_n8n --format"
        " '{{range .Config.Env}}{{println .}}{{end}}'"
        " 2>/dev/null | grep -i"
        " 'n8n\\|secure\\|cookie\\|webhook\\|auth'"
        " || echo 'No ultra_n8n'",
    ),
    (
        "n8n container env",
        "docker inspect n8n --format"
        " '{{range .Config.Env}}{{println .}}{{end}}'"
        " 2>/dev/null | head -20"
        " || echo 'No n8n container'",
    ),
    ("Docker compose files", "find /opt /root -name 'docker-compose*' -type f 2>/dev/null | head -10"),
    ("n8n health", "curl -s http://localhost:5678/healthz 2>/dev/null"),
]

for label, cmd in cmds:
    print(f"\n=== {label} ===")
    _, o, e = ssh.exec_command(cmd)
    print(o.read().decode().strip())

ssh.close()
