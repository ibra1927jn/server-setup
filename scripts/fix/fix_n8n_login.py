import json
import time
from shared_config import get_ssh_client, N8N_EMAIL, N8N_PASSWORD


def main():
    ssh = get_ssh_client()

    # Check the docker-compose env for n8n credentials
    _, o, _ = ssh.exec_command("cat /root/n8n/.env")
    print("=== N8N DOCKER ENV ===")
    env_content = o.read().decode()
    print(env_content)

    # Try login with credentials from .env
    login_payload = json.dumps({"emailOrLdapLoginId": N8N_EMAIL, "password": N8N_PASSWORD})
    cmd = f'''curl -s -c /tmp/n8n_cookies.txt -X POST http://127.0.0.1:5678/rest/login \
      -H "Content-Type: application/json" \
      -d '{login_payload}' '''
    _, o2, _ = ssh.exec_command(cmd)
    time.sleep(2)
    login_resp = o2.read().decode()
    print("\n=== LOGIN RESPONSE ===")
    print(login_resp[:500])

    ssh.close()


if __name__ == "__main__":
    main()
