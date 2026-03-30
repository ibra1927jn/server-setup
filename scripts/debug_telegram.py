"""
Debug: por que no llegan mensajes de Telegram.
Verificar: credenciales, IDs de credencial, ejecuciones, errores.
"""
import json

from shared_config import get_ssh_client


def main():
    ssh = get_ssh_client()

    # 1. Check what credentials exist
    print("=== CREDENCIALES EN N8N ===")
    _, o, _ = ssh.exec_command("docker exec n8n-n8n-1 n8n export:credentials --all")
    creds_raw = o.read().decode().strip()
    try:
        creds = json.loads(creds_raw)
        if isinstance(creds, list):
            for c in creds:
                print(f"  ID: {c.get('id')} | Name: {c.get('name')} | Type: {c.get('type')}")
        else:
            print(f"  {creds_raw[:300]}")
    except Exception:
        print(f"  Raw: {creds_raw[:300]}")

    # 2. Export all workflows and check telegram node credential IDs
    print("\n=== TELEGRAM NODES EN WORKFLOWS ===")
    _, o, _ = ssh.exec_command("docker exec n8n-n8n-1 n8n export:workflow --all")
    raw = o.read().decode().strip()
    all_wfs = json.loads(raw)

    for wf in all_wfs:
        name = wf.get("name", "")
        for node in wf.get("nodes", []):
            if "telegram" in node.get("type", "").lower():
                cred = node.get("credentials", {})
                params = node.get("parameters", {})
                chat_id = params.get("chatId", "?")
                text_preview = str(params.get("text", "?"))[:80]
                print(f"\n  WF: {name}")
                print(f"  Node: {node['name']}")
                print(f"  ChatID: {chat_id}")
                print(f"  Creds: {json.dumps(cred)}")
                print(f"  Text: {text_preview}")

    # 3. Check execution history - look for errors
    print("\n=== ULTIMAS EJECUCIONES ===")
    _, o, _ = ssh.exec_command(
        'docker exec n8n-n8n-1 sh -c "sqlite3'
        " /home/node/.n8n/database.sqlite"
        " 'SELECT id, workflowId, status, stoppedAt"
        ' FROM execution_entity ORDER BY id DESC LIMIT 15;\'"'
    )
    execs = o.read().decode().strip()
    print(execs if execs else "  (no sqlite3 or no data)")

    # 4. Try a direct Telegram test from the server
    print("\n=== TEST DIRECTO TELEGRAM ===")
    # Find the Telegram bot token from credentials
    _, o, _ = ssh.exec_command("docker exec n8n-n8n-1 n8n export:credentials --all --decrypted 2>/dev/null")
    decrypted = o.read().decode().strip()
    try:
        all_creds = json.loads(decrypted)
        for c in all_creds:
            if "telegram" in c.get("type", "").lower():
                token_data = c.get("data", {})
                print(f"  Telegram cred: {c.get('name')} (ID: {c.get('id')})")
                print(f"  Token preview: {str(token_data)[:50]}...")
    except Exception:
        print("  Could not decrypt credentials (expected)")

    # Try sending via curl with known bot token from previous session
    print("\n  Testing via API...")
    test_cmd = (
        "docker exec n8n-n8n-1 sh -c 'curl -s"
        ' "https://api.telegram.org/bot$(cat /tmp/tg_test'
        " 2>/dev/null || echo NOTOKEN)/getMe\""
        " 2>/dev/null'"
    )
    _, o, _ = ssh.exec_command(test_cmd)
    print(f"  {o.read().decode().strip()[:200]}")

    # 5. Check if n8n execute actually ran
    print("\n=== N8N CONTAINER LOGS (last 30 lines) ===")
    _, o, _ = ssh.exec_command("docker logs n8n-n8n-1 --tail 30 2>&1")
    logs = o.read().decode().strip()
    # Filter for relevant lines
    for line in logs.split("\n"):
        if any(kw in line.lower() for kw in ["error", "fail", "telegram", "execut", "workflow", "credential"]):
            print(f"  {line.strip()}")

    ssh.close()
    print("\nDone!")


if __name__ == "__main__":
    main()
