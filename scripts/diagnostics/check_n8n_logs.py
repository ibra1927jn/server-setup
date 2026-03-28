from shared_config import get_ssh_client

ssh = get_ssh_client()

# Get the last 50 lines of n8n logs
_, o, _ = ssh.exec_command("docker logs n8n-n8n-1 --tail=50 2>&1")
print(o.read().decode())

ssh.close()
