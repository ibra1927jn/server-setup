from shared_config import get_ssh_client

ssh = get_ssh_client()

# Read the current dashboard HTML
_, o, _ = ssh.exec_command("cat /var/www/dashboard/index.html")
current_html = o.read().decode()

# Fix the JSON payload: change "message" to "chatInput"
fixed_html = current_html.replace(
    "body: JSON.stringify({message: msg})",
    "body: JSON.stringify({chatInput: msg})"
)

# Upload the fixed version
with ssh.open_sftp() as sftp:
    with sftp.file('/var/www/dashboard/index.html', 'w') as f:
        f.write(fixed_html)

print("Fixed! Changed 'message' -> 'chatInput' in webhook payload")

# Test the webhook with the correct field
import time
time.sleep(1)
cmd = '''curl -s -k -X POST https://127.0.0.1/webhook/ai-agent \
  -H "Content-Type: application/json" \
  -H "Host: 95.217.158.7" \
  -d '{"chatInput": "Di solamente OK"}' '''
_, o2, _ = ssh.exec_command(cmd)
import time
time.sleep(15)  # Give AI time to respond
print("\n=== WEBHOOK TEST WITH chatInput ===")
print(o2.read().decode())

ssh.close()
