import time
from shared_config import get_ssh_client

ssh = get_ssh_client()

# First find what user exists
_, o, _ = ssh.exec_command("docker exec n8n-n8n-1 n8n user-management:list 2>&1 || echo 'list not available'")
time.sleep(3)
print("=== USER LIST ===")
print(o.read().decode())

# Try the db:revert approach or env var approach
# The simplest way: stop n8n, set env var to reset, restart
# Or use the n8n CLI built-in password reset

# Check available CLI commands
_, o2, _ = ssh.exec_command("docker exec n8n-n8n-1 n8n --help 2>&1")
time.sleep(3)
help_text = o2.read().decode()
print("=== N8N CLI COMMANDS ===")
# Filter for relevant lines
for line in help_text.split('\n'):
    if 'user' in line.lower() or 'pass' in line.lower() or 'reset' in line.lower():
        print(line)

ssh.close()
