import json
import time
from shared_config import get_ssh_client

ssh = get_ssh_client()

# Check the docker-compose env for n8n credentials
_, o, _ = ssh.exec_command("cat /root/n8n/.env")
print("=== N8N DOCKER ENV ===")
env_content = o.read().decode()
print(env_content)

# Try login with correct API format
cmd = '''curl -s -c /tmp/n8n_cookies.txt -X POST http://127.0.0.1:5678/rest/login \
  -H "Content-Type: application/json" \
  -d '{"emailOrLdapLoginId":"ibrahim@alz.agency","password":"admin123"}' '''
_, o2, _ = ssh.exec_command(cmd)
time.sleep(2)
login_resp = o2.read().decode()
print("\n=== LOGIN RESPONSE ===")
print(login_resp[:500])

# If failed, try with ibra as user
if 'error' in login_resp.lower() or 'unauthorized' in login_resp.lower():
    cmd2 = '''curl -s -c /tmp/n8n_cookies.txt -X POST http://127.0.0.1:5678/rest/login \
      -H "Content-Type: application/json" \
      -d '{"emailOrLdapLoginId":"ibra","password":"admin123"}' '''
    _, o3, _ = ssh.exec_command(cmd2)
    time.sleep(2)
    print("\n=== LOGIN AS IBRA ===")
    print(o3.read().decode()[:500])

ssh.close()
