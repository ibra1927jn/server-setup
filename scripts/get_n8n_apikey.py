from shared_config import get_ssh_client

ssh = get_ssh_client()

# Get n8n API key
_, o, _ = ssh.exec_command("docker exec n8n-n8n-1 cat /home/node/.n8n/.env 2>/dev/null || echo 'no .env'")
print(o.read().decode())

# Try to get API key from n8n settings
_, o, _ = ssh.exec_command("docker exec n8n-n8n-1 grep -r 'N8N_API_KEY\\|api_key' /home/node/.n8n/ 2>/dev/null | head -5")
print(o.read().decode())

# Check env vars from docker-compose
_, o, _ = ssh.exec_command("cat /root/n8n/docker-compose.yml | grep -A5 N8N")
print("=== DOCKER COMPOSE N8N VARS ===")
print(o.read().decode())

# Get the API key from the n8n container env
_, o, _ = ssh.exec_command("docker exec n8n-n8n-1 env | grep N8N")
print("=== N8N ENV VARS ===")
print(o.read().decode())

ssh.close()
