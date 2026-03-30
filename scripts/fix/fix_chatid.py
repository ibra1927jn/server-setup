"""
FIX DEFINITIVO: El chatID en los workflows esta mal.
.env tiene 5822131920, workflows tienen 6915862027.
Primero test directo, luego parchar todos los workflows.
"""

import json
import time

import requests
from shared_config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, get_ssh_client

REAL_CHAT_ID = TELEGRAM_CHAT_ID
WRONG_CHAT_ID = "6915862027"


def test_send_message(url, chat_id, text):
    """Send a test message and print result."""
    r = requests.post(
        url,
        json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown",
        },
        timeout=30,
    )
    print(f"  Status: {r.status_code}")
    print(f"  Response: {r.text[:300]}")
    return r


def fix_workflow_chat_ids(wf):
    """Replace WRONG_CHAT_ID with REAL_CHAT_ID in all nodes. Returns True if changed."""
    changed = False
    name = wf.get("name", "")
    for node in wf.get("nodes", []):
        params = node.get("parameters", {})
        if "chatId" in params and params["chatId"] == WRONG_CHAT_ID:
            print(f"  [{name}] {node['name']}: chatId {params['chatId']} -> {REAL_CHAT_ID}")
            params["chatId"] = REAL_CHAT_ID
            changed = True
        text = params.get("text", "")
        if WRONG_CHAT_ID in str(text):
            params["text"] = str(text).replace(WRONG_CHAT_ID, REAL_CHAT_ID)
            changed = True
    return changed


def upload_and_import_fix(ssh, sftp, wf, name):
    """Upload fixed workflow and import into n8n."""
    fname = f"fix_{name.lower().replace(' ', '_')}.json"
    local_path = f"C:\\Users\\ibrab\\Desktop\\set up\\scripts\\{fname}"
    remote_path = f"/tmp/{fname}"

    with open(local_path, "w", encoding="utf-8") as f:
        json.dump(wf, f)

    sftp.put(local_path, remote_path)
    ssh.exec_command(f"docker cp {remote_path} n8n-n8n-1:/tmp/{fname}")
    time.sleep(1)
    cmd = f"docker exec n8n-n8n-1 n8n import:workflow --input=/tmp/{fname}"
    _, o, _e = ssh.exec_command(cmd)
    print(f"    Import: {o.read().decode().strip()}")


def main():
    print("=== TEST LOCAL: Enviar mensaje directo ===")
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    r = test_send_message(
        url,
        REAL_CHAT_ID,
        "🧪 Test AgenticOS - Chat ID CORRECTO (5822131920). Si ves esto, Telegram funciona!",
    )

    if r.status_code == 200 and r.json().get("ok"):
        print("  ✅ MENSAJE ENVIADO! El chatID correcto es 5822131920")
    else:
        print("  ❌ Fallo. Probando getUpdates...")
        url2 = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?limit=5"
        r2 = requests.get(url2, timeout=30)
        print(f"  Updates: {r2.text[:500]}")

    print(f"\n=== TEST: chatID incorrecto ({WRONG_CHAT_ID}) ===")
    test_send_message(url, WRONG_CHAT_ID, "Test con ID incorrecto")

    print("\n=== PARCHANDO TODOS LOS WORKFLOWS ===")
    ssh = get_ssh_client()
    _, o, _ = ssh.exec_command("docker exec n8n-n8n-1 n8n export:workflow --all")
    all_wfs = json.loads(o.read().decode().strip())

    sftp = ssh.open_sftp()
    fixed_count = 0
    for wf in all_wfs:
        if fix_workflow_chat_ids(wf):
            upload_and_import_fix(ssh, sftp, wf, wf.get("name", ""))
            fixed_count += 1
    print(f"\n  Workflows parcheados: {fixed_count}")

    print("\n=== RESTART ===")
    ssh.exec_command("docker restart n8n-n8n-1")
    time.sleep(12)
    cmd = "docker exec n8n-n8n-1 n8n update:workflow --all --active=true"
    _, o, _ = ssh.exec_command(cmd)
    o.read()
    print("  Reiniciado y activado!")

    print("\n=== TEST FINAL: Ejecutar Crypto Portfolio Alerts ===")
    for wf in all_wfs:
        if "Crypto" in wf.get("name", ""):
            print(f"  Ejecutando {wf['name']}...")
            cmd = f"docker exec n8n-n8n-1 n8n execute --id={wf['id']} 2>&1"
            _, o, _e = ssh.exec_command(cmd, timeout=30)
            try:
                print(f"  {o.read().decode().strip()[:200]}")
            except Exception:
                print("  (timeout)")
            break

    sftp.close()
    ssh.close()
    print("\n=== HECHO! Revisa tu Telegram AHORA ===")


if __name__ == "__main__":
    main()
