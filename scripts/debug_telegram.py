"""
Debug: por que no llegan mensajes de Telegram.
Verificar: credenciales, IDs de credencial, ejecuciones, errores.
"""

import json

from shared_config import get_ssh_client


def print_credentials(ssh):
    """Print all n8n credentials."""
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


def print_telegram_nodes(all_wfs):
    """Print Telegram node details from all workflows."""
    print("\n=== TELEGRAM NODES EN WORKFLOWS ===")
    for wf in all_wfs:
        name = wf.get("name", "")
        for node in wf.get("nodes", []):
            if "telegram" in node.get("type", "").lower():
                params = node.get("parameters", {})
                print(f"\n  WF: {name}")
                print(f"  Node: {node['name']}")
                print(f"  ChatID: {params.get('chatId', '?')}")
                print(f"  Creds: {json.dumps(node.get('credentials', {}))}")
                print(f"  Text: {str(params.get('text', '?'))[:80]}")


def print_execution_history(ssh):
    """Print recent n8n execution history from SQLite."""
    print("\n=== ULTIMAS EJECUCIONES ===")
    _, o, _ = ssh.exec_command(
        'docker exec n8n-n8n-1 sh -c "sqlite3'
        " /home/node/.n8n/database.sqlite"
        " 'SELECT id, workflowId, status, stoppedAt"
        " FROM execution_entity ORDER BY id DESC LIMIT 15;'\""
    )
    execs = o.read().decode().strip()
    print(execs or "  (no sqlite3 or no data)")


def print_telegram_creds(ssh):
    """Print decrypted Telegram credentials and test API access."""
    print("\n=== TEST DIRECTO TELEGRAM ===")
    cmd = "docker exec n8n-n8n-1 n8n export:credentials --all --decrypted 2>/dev/null"
    _, o, _ = ssh.exec_command(cmd)
    decrypted = o.read().decode().strip()
    try:
        all_creds = json.loads(decrypted)
        for c in all_creds:
            if "telegram" in c.get("type", "").lower():
                token_data = c.get("data", {})
                print(f"  Telegram cred: {c.get('name')} (ID: {c.get('id')})")
                print(f"  Telegram cred data found: {len(token_data)} fields")
    except Exception:
        print("  Could not decrypt credentials (expected)")

    print("\n  Testing via API...")
    test_cmd = (
        "docker exec n8n-n8n-1 sh -c 'curl -s"
        ' "https://api.telegram.org/bot$(cat /tmp/tg_test'
        ' 2>/dev/null || echo NOTOKEN)/getMe"'
        " 2>/dev/null'"
    )
    _, o, _ = ssh.exec_command(test_cmd)
    print(f"  {o.read().decode().strip()[:200]}")


def print_relevant_logs(ssh):
    """Print n8n container log lines matching error/telegram keywords."""
    print("\n=== N8N CONTAINER LOGS (last 30 lines) ===")
    _, o, _ = ssh.exec_command("docker logs n8n-n8n-1 --tail 30 2>&1")
    logs = o.read().decode().strip()
    for line in logs.split("\n"):
        keywords = [
            "error",
            "fail",
            "telegram",
            "execut",
            "workflow",
            "credential",
        ]
        if any(kw in line.lower() for kw in keywords):
            print(f"  {line.strip()}")


def main():
    ssh = get_ssh_client()

    print_credentials(ssh)

    _, o, _ = ssh.exec_command("docker exec n8n-n8n-1 n8n export:workflow --all")
    all_wfs = json.loads(o.read().decode().strip())
    print_telegram_nodes(all_wfs)

    print_execution_history(ssh)
    print_telegram_creds(ssh)
    print_relevant_logs(ssh)

    ssh.close()
    print("\nDone!")


if __name__ == "__main__":
    main()
