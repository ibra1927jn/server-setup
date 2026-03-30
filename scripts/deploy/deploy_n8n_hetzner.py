"""Deploy n8n to Hetzner VPS via Docker Compose"""

import time

from shared_config import N8N_EMAIL, N8N_PASSWORD, VPS_HOST, get_ssh_client

DOCKER_COMPOSE_TEMPLATE = """version: '3.8'

services:
  n8n:
    image: n8nio/n8n:latest
    container_name: n8n
    restart: always
    ports:
      - "5678:5678"
    environment:
      - N8N_HOST=0.0.0.0
      - N8N_PORT=5678
      - N8N_PROTOCOL=http
      - WEBHOOK_URL=http://{vps_host}:5678/
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER={n8n_user}
      - N8N_BASIC_AUTH_PASSWORD={n8n_password}
      - GENERIC_TIMEZONE=Europe/Madrid
      - TZ=Europe/Madrid
      - N8N_DIAGNOSTICS_ENABLED=false
      - N8N_PERSONALIZATION_ENABLED=false
    volumes:
      - n8n_data:/home/node/.n8n

volumes:
  n8n_data:
    driver: local
"""

NGINX_CONF = """server {
    listen 80;
    server_name n8n.alz.agency;

    location / {
        proxy_pass http://localhost:5678;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
        proxy_buffering off;
        client_max_body_size 50M;
    }
}
"""


def run(ssh, cmd, label="", timeout=120):
    if label:
        print(f"\n{'=' * 50}")
        print(f"  {label}")
        print(f"{'=' * 50}")
    print(f"$ {cmd[:100]}")
    _, o, e = ssh.exec_command(cmd, timeout=timeout)
    out = o.read().decode().strip()
    err = e.read().decode().strip()
    if out:
        print(out)
    if err and "WARNING" not in err and "warn" not in err.lower():
        print(f"[stderr] {err}")
    return out


def main():
    print(f"Connecting to {VPS_HOST}...")
    ssh = get_ssh_client()
    sftp = ssh.open_sftp()

    # 1. Create n8n directory
    run(ssh, "mkdir -p /opt/n8n", "Creating /opt/n8n")

    # 2. Write docker-compose.yml
    print("\n=== Writing docker-compose.yml ===")
    docker_compose = DOCKER_COMPOSE_TEMPLATE.format(
        vps_host=VPS_HOST,
        n8n_user=N8N_EMAIL or "admin",
        n8n_password=N8N_PASSWORD,
    )
    with sftp.open("/opt/n8n/docker-compose.yml", "w") as f:
        f.write(docker_compose)
    print("Written to /opt/n8n/docker-compose.yml")

    # 3. Write nginx config
    print("\n=== Writing Nginx config ===")
    with sftp.open("/etc/nginx/sites-available/n8n", "w") as f:
        f.write(NGINX_CONF)
    print("Written to /etc/nginx/sites-available/n8n")

    # 4. Enable nginx site
    run(ssh, "ln -sf /etc/nginx/sites-available/n8n /etc/nginx/sites-enabled/n8n", "Enable Nginx site")
    run(ssh, "nginx -t 2>&1", "Test Nginx config")
    run(ssh, "systemctl reload nginx 2>&1", "Reload Nginx")

    # 5. Pull and start n8n
    run(ssh, "cd /opt/n8n && docker compose pull 2>&1 | tail -5", "Pulling n8n Docker image")
    run(ssh, "cd /opt/n8n && docker compose down 2>&1", "Stopping old container (if any)")
    run(ssh, "cd /opt/n8n && docker compose up -d 2>&1", "Starting n8n container")

    # 6. Wait for n8n to start
    print("\n=== Waiting for n8n to start (30s) ===")
    time.sleep(30)

    # 7. Verify
    run(ssh, "docker ps --filter name=n8n --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'", "Container status")
    health_cmd = "curl -s -o /dev/null -w '%{http_code}' http://localhost:5678/ 2>/dev/null || echo 'NOT_READY'"
    run(ssh, health_cmd, "Health check")

    sftp.close()
    ssh.close()
    print("\n=== DEPLOYMENT COMPLETE ===")
    print(f"n8n URL: http://{VPS_HOST}:5678")
    print(f"Auth: {N8N_EMAIL or 'admin'} / ***")


if __name__ == "__main__":
    main()
