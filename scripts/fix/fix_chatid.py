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


def main():
    # TEST 1: Send directly from this PC
    print("=== TEST LOCAL: Enviar mensaje directo ===")
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    r = requests.post(url, json={
        "chat_id": REAL_CHAT_ID,
        "text": "🧪 Test AgenticOS - Chat ID CORRECTO (5822131920). Si ves esto, Telegram funciona!",
        "parse_mode": "Markdown"
    })
    print(f"  Status: {r.status_code}")
    print(f"  Response: {r.text[:300]}")

    if r.status_code == 200 and r.json().get("ok"):
        print("  ✅ MENSAJE ENVIADO! El chatID correcto es 5822131920")
    else:
        print("  ❌ Fallo. Probando getUpdates para encontrar tu chatID real...")
        r2 = requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?limit=5")
        print(f"  Updates: {r2.text[:500]}")

    # TEST 2: Also test with wrong chatID to confirm it's the issue
    print(f"\n=== TEST: chatID incorrecto ({WRONG_CHAT_ID}) ===")
    r3 = requests.post(url, json={
        "chat_id": WRONG_CHAT_ID,
        "text": "Test con ID incorrecto"
    })
    print(f"  Status: {r3.status_code}")
    print(f"  Response: {r3.text[:200]}")

    # NOW FIX ALL WORKFLOWS
    print("\n=== PARCHANDO TODOS LOS WORKFLOWS ===")
    ssh = get_ssh_client()

    _, o, _ = ssh.exec_command("docker exec n8n-n8n-1 n8n export:workflow --all")
    all_wfs = json.loads(o.read().decode().strip())

    sftp = ssh.open_sftp()
    fixed_count = 0

    for wf in all_wfs:
        name = wf.get("name", "")
        changed = False

        for node in wf.get("nodes", []):
            params = node.get("parameters", {})

            # Fix chatId wherever it appears
            if "chatId" in params:
                old_id = params["chatId"]
                if old_id == WRONG_CHAT_ID:
                    params["chatId"] = REAL_CHAT_ID
                    print(f"  [{name}] {node['name']}: chatId {old_id} -> {REAL_CHAT_ID}")
                    changed = True

            # Also check in text field for hardcoded references
            text = params.get("text", "")
            if WRONG_CHAT_ID in str(text):
                params["text"] = str(text).replace(WRONG_CHAT_ID, REAL_CHAT_ID)
                changed = True

        if changed:
            fname = f"fix_{name.lower().replace(' ', '_')}.json"
            local_path = f"C:\\Users\\ibrab\\Desktop\\set up\\scripts\\{fname}"
            remote_path = f"/tmp/{fname}"

            with open(local_path, "w", encoding="utf-8") as f:
                json.dump(wf, f)

            sftp.put(local_path, remote_path)
            ssh.exec_command(f"docker cp {remote_path} n8n-n8n-1:/tmp/{fname}")
            time.sleep(1)
            _, o, e = ssh.exec_command(f"docker exec n8n-n8n-1 n8n import:workflow --input=/tmp/{fname}")
            print(f"    Import: {o.read().decode().strip()}")
            fixed_count += 1

    print(f"\n  Workflows parcheados: {fixed_count}")

    # Restart
    print("\n=== RESTART ===")
    ssh.exec_command("docker restart n8n-n8n-1")
    time.sleep(12)
    _, o, _ = ssh.exec_command("docker exec n8n-n8n-1 n8n update:workflow --all --active=true")
    o.read()
    print("  Reiniciado y activado!")

    # Final test: Execute Crypto Portfolio Alerts
    print("\n=== TEST FINAL: Ejecutar Crypto Portfolio Alerts ===")
    for wf in all_wfs:
        if "Crypto" in wf.get("name", ""):
            print(f"  Ejecutando {wf['name']}...")
            _, o, e = ssh.exec_command(f"docker exec n8n-n8n-1 n8n execute --id={wf['id']} 2>&1", timeout=30)
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
