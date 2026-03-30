import time

from shared_config import get_ssh_client


def main():
    ssh = get_ssh_client()

    # Restart n8n
    print("Restarting n8n...")
    ssh.exec_command("cd /root/n8n && docker compose restart")
    time.sleep(15)

    # Check status
    _, o, _ = ssh.exec_command("docker ps --format '{{.Names}} {{.Status}}'")
    print("=== CONTAINERS ===")
    print(o.read().decode())

    # Wait a bit more for n8n to fully start
    time.sleep(10)

    # Test the webhook
    print("\n=== TESTING WEBHOOK ===")
    cmd = '''curl -s -X POST http://127.0.0.1:5678/webhook/ai-agent \
      -H "Content-Type: application/json" \
      -d '{"chatInput": "Di simplemente OK"}' --max-time 45'''
    _, o2, _ = ssh.exec_command(cmd)
    time.sleep(30)
    response = o2.read().decode()
    print("RESPONSE:", response)

    ssh.close()


if __name__ == "__main__":
    main()
