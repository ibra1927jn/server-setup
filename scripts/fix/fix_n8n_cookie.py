"""Fix n8n secure cookie issue on Hetzner"""
import time
from shared_config import get_ssh_client

DOCKER_COMPOSE = """version: '3.8'

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
      - WEBHOOK_URL=http://95.217.158.7:5678/
      - N8N_SECURE_COOKIE=false
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


def main():
    ssh = get_ssh_client()
    sftp = ssh.open_sftp()

    print("Writing updated docker-compose.yml...")
    with sftp.open("/opt/n8n/docker-compose.yml", "w") as f:
        f.write(DOCKER_COMPOSE)

    print("Restarting n8n container...")
    _, o, e = ssh.exec_command("cd /opt/n8n && docker compose down && docker compose up -d 2>&1", timeout=60)
    print(o.read().decode())

    print("Waiting 15s for n8n to start...")
    time.sleep(15)

    _, o, e = ssh.exec_command("curl -s -o /dev/null -w '%{http_code}' http://localhost:5678/setup")
    print(f"Setup page HTTP code: {o.read().decode()}")

    _, o, e = ssh.exec_command("docker ps --filter name=n8n --format 'table {{.Names}}\t{{.Status}}'")
    print(o.read().decode())

    sftp.close()
    ssh.close()
    print("Done!")


if __name__ == "__main__":
    main()
