from shared_config import get_ssh_client

ssh = get_ssh_client()

# Check docker-compose.yml for credential setup
_, o, _ = ssh.exec_command("cat /root/n8n/docker-compose.yml")
print("=== DOCKER COMPOSE ===")
print(o.read().decode())

ssh.close()
