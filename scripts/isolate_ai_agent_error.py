import time

from shared_config import (
    N8N_AI_WORKFLOW_ID,
    N8N_TELEGRAM_BOT_WORKFLOW_ID,
    get_ssh_client,
)


def main():
    ssh = get_ssh_client()

    print("=== DEACTIVATING TELEGRAM BOT ===")
    sqlite_cmd = (
        "docker exec n8n-n8n-1 sqlite3"
        " /home/node/.n8n/database.sqlite"
        ' "UPDATE workflow_entity SET active = 0'
        f" WHERE id = '{N8N_TELEGRAM_BOT_WORKFLOW_ID}';\""
    )
    ssh.exec_command(sqlite_cmd)

    # And AI Agent Base might be active, let's keep it active
    sqlite_cmd2 = (
        "docker exec n8n-n8n-1 sqlite3"
        " /home/node/.n8n/database.sqlite"
        f' "UPDATE workflow_entity SET active = 1'
        f" WHERE id = '{N8N_AI_WORKFLOW_ID}';\""
    )
    ssh.exec_command(sqlite_cmd2)

    time.sleep(1)
    print("=== RESTARTING N8N ===")
    ssh.exec_command("docker restart n8n-n8n-1")
    time.sleep(15)  # give n8n time to start

    print("=== TRIGGERING AI AGENT WEBHOOK ===")
    _, o, _ = ssh.exec_command("""curl -s -X POST http://127.0.0.1:5678/webhook/ai-agent \
      -H "Content-Type: application/json" \
      -d '{"chatInput": "Hello IA"}' """)
    print("WEBHOOK RESPONSE:", o.read().decode())

    print("=== GETTING RECENT LOGS ===")
    _, o2, _ = ssh.exec_command("docker logs n8n-n8n-1 --tail 50")
    print("LOGS:", o2.read().decode()[-2000:])

    ssh.close()


if __name__ == "__main__":
    main()
