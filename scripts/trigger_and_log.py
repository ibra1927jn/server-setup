import time

from shared_config import get_ssh_client


def main():
    ssh = get_ssh_client()

    # Clear the last lines so we have a clean log
    print("=== TRIGGER TEST AND CHECK LOGS ===")
    # First, trigger the webhook
    _, o, _ = ssh.exec_command('''curl -s -X POST http://127.0.0.1:5678/webhook/ai-agent \
      -H "Content-Type: application/json" \
      -d '{"chatInput": "test"}' --max-time 30 &
    sleep 10
    docker logs n8n-n8n-1 --since 10s 2>&1 | tail -30''')
    time.sleep(15)
    print(o.read().decode())

    ssh.close()


if __name__ == "__main__":
    main()
