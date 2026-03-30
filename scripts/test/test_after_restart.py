import time

from shared_config import get_ssh_client


def main():
    ssh = get_ssh_client()

    # Test the AI webhook after restart
    print("=== TESTING AI WEBHOOK ===")
    cmd = '''curl -s -X POST http://127.0.0.1:5678/webhook/ai-agent \
      -H "Content-Type: application/json" \
      -d '{"chatInput": "Di simplemente OK"}' --max-time 45'''
    _, o, _ = ssh.exec_command(cmd)
    time.sleep(30)
    result = o.read().decode()
    print("RESPONSE:", result[:500])

    # Also check all workflow statuses
    print("\n=== WORKFLOW STATUSES ===")
    _, o2, _ = ssh.exec_command("docker exec n8n-n8n-1 n8n list:workflow 2>&1 | tail -20")
    time.sleep(3)
    print(o2.read().decode())

    ssh.close()


if __name__ == "__main__":
    main()
