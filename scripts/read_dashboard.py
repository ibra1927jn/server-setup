from shared_config import get_ssh_client

ssh = get_ssh_client()

# Read the current dashboard HTML
_, o, _ = ssh.exec_command("cat /var/www/dashboard/index.html")
current_html = o.read().decode()
print(f"Dashboard HTML length: {len(current_html)} chars")
print("Last 200 chars:", current_html[-200:])

ssh.close()
