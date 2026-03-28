"""Check DNS, ports, and nginx status on Hetzner"""
from shared_config import get_ssh_client

ssh = get_ssh_client()

checks = [
    ("DNS alz.agency", "dig +short alz.agency A 2>/dev/null || host alz.agency 2>/dev/null || echo 'no_dns_tool'"),
    ("Nginx", "which nginx 2>/dev/null && nginx -v 2>&1 || echo 'NO_NGINX'"),
    ("Caddy", "which caddy 2>/dev/null || echo 'NO_CADDY'"),
    ("Ports 80/443/5678", "ss -tlnp | grep -E '(80|443|5678)'"),
    ("Docker containers", "docker ps --format '{{.Names}} {{.Status}}'"),
    ("Certbot", "which certbot 2>/dev/null || echo 'NO_CERTBOT'"),
]

for name, cmd in checks:
    print(f"=== {name} ===")
    _, o, e = ssh.exec_command(cmd)
    out = o.read().decode().strip()
    if out:
        print(out)
    else:
        print("(empty)")
    print()

ssh.close()
