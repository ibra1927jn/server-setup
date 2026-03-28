import time
from shared_config import get_ssh_client, N8N_EMAIL, N8N_PASSWORD

ssh = get_ssh_client()

# Restart n8n to clear any cached sessions
ssh.exec_command("cd /root/n8n && docker compose restart")
time.sleep(20)

# Test login
login_cmd = f'''curl -s -X POST http://127.0.0.1:5678/rest/login \
  -H "Content-Type: application/json" \
  -d '{{"emailOrLdapLoginId":"{N8N_EMAIL}","password":"{N8N_PASSWORD}"}}' '''
_, o, _ = ssh.exec_command(login_cmd)
time.sleep(3)
login_result = o.read().decode()
print("=== LOGIN RESULT ===")
print(login_result[:500])

if '"id"' in login_result and 'ibrahim' in login_result.lower():
    print("\n✅ PASSWORD RESET SUCCESSFUL!")
else:
    print("\n❌ Login still failing")

ssh.close()
