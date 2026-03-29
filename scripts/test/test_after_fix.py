import time
from shared_config import get_ssh_client


def main():
    ssh = get_ssh_client()

    # Test the AI webhook
    print("=== TESTING WEBHOOK AFTER FIX ===")
    cmd = '''curl -s -X POST http://127.0.0.1:5678/webhook/ai-agent \
      -H "Content-Type: application/json" \
      -d '{"chatInput": "Di simplemente OK"}' --max-time 60'''
    _, o, _ = ssh.exec_command(cmd)
    time.sleep(45)
    result = o.read().decode()
    print("RESPONSE:", result[:500])

    if 'Error' in result:
        print("\n=== N8N RECENT LOGS ===")
        _, o2, _ = ssh.exec_command("docker logs n8n-n8n-1 --tail=20 2>&1")
        time.sleep(2)
        print(o2.read().decode()[:1000])

    ssh.close()


if __name__ == "__main__":
    main()
