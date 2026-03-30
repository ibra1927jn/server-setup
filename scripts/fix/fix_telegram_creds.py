"""
Fix: Obtener IDs reales de credenciales y parchear TODOS los workflows nuevos.
"""
import json
import time
from shared_config import get_ssh_client

ssh = get_ssh_client()

# 1. Get REAL credential IDs
print("=== CREDENCIALES REALES ===")
_, o, _ = ssh.exec_command("docker exec n8n-n8n-1 n8n export:credentials --all")
creds_raw = o.read().decode().strip()
creds = json.loads(creds_raw)

real_creds = {}
for c in creds:
    cid = c.get("id", "")
    cname = c.get("name", "")
    ctype = c.get("type", "")
    print(f"  {cid} | {cname} | {ctype}")
    real_creds[ctype] = {"id": cid, "name": cname}

# 2. Get REAL telegram credential
telegram_cred = real_creds.get("telegramApi", {})
ssh_cred = real_creds.get("sshPassword", {})
print(f"\n  Telegram real: {telegram_cred}")
print(f"  SSH real: {ssh_cred}")

if not telegram_cred.get("id"):
    print("\n  ERROR: No telegram credential found!")
    ssh.close()
    exit(1)

# 3. Export all workflows and fix credentials
print("\n=== PARCHANDO WORKFLOWS ===")
_, o, _ = ssh.exec_command("docker exec n8n-n8n-1 n8n export:workflow --all")
all_wfs = json.loads(o.read().decode().strip())

sftp = ssh.open_sftp()
workflows_to_fix = ["Daily Briefing", "Uptime Monitor", "Crypto Portfolio Alerts", "GitHub Auto-Backup"]

for wf in all_wfs:
    name = wf.get("name", "")
    if name not in workflows_to_fix:
        continue

    print(f"\n--- {name} ---")
    changed = False

    for node in wf.get("nodes", []):
        ntype = node.get("type", "")

        # Fix Telegram credentials
        if "telegram" in ntype.lower():
            old_cred = node.get("credentials", {}).get("telegramApi", {})
            print(f"  Telegram node '{node['name']}': old ID={old_cred.get('id')}, real ID={telegram_cred['id']}")
            node["credentials"] = {
                "telegramApi": {
                    "id": telegram_cred["id"],
                    "name": telegram_cred["name"]
                }
            }
            changed = True

        # Fix SSH credentials
        if "ssh" in ntype.lower() and ssh_cred.get("id"):
            old_cred = node.get("credentials", {}).get("sshPassword", {})
            print(f"  SSH node '{node['name']}': old ID={old_cred.get('id')}, real ID={ssh_cred['id']}")
            node["credentials"] = {
                "sshPassword": {
                    "id": ssh_cred["id"],
                    "name": ssh_cred["name"]
                }
            }
            changed = True

    if changed:
        fname = name.lower().replace(" ", "_") + "_fixed.json"
        local_path = f"C:\\Users\\ibrab\\Desktop\\set up\\scripts\\{fname}"
        remote_path = f"/tmp/{fname}"

        with open(local_path, "w", encoding="utf-8") as f:
            json.dump(wf, f)

        sftp.put(local_path, remote_path)
        ssh.exec_command(f"docker cp {remote_path} n8n-n8n-1:/tmp/{fname}")
        time.sleep(1)
        _, o, e = ssh.exec_command(f"docker exec n8n-n8n-1 n8n import:workflow --input=/tmp/{fname}")
        result = o.read().decode().strip()
        print(f"  Import: {result}")

# 4. Restart and activate
print("\n=== RESTART + ACTIVATE ===")
ssh.exec_command("docker restart n8n-n8n-1")
time.sleep(12)

_, o, _ = ssh.exec_command("docker exec n8n-n8n-1 n8n update:workflow --all --active=true")
o.read()
print("  All activated!")

# 5. TEST: Execute Crypto Portfolio Alerts (simplest, no SSH needed)
print("\n=== TEST RAPIDO: Crypto Portfolio Alerts ===")
for wf in all_wfs:
    if "Crypto" in wf.get("name", ""):
        wf_id = wf["id"]
        print(f"  Executing {wf_id}...")
        _, o, e = ssh.exec_command(f"docker exec n8n-n8n-1 n8n execute --id={wf_id} 2>&1", timeout=30)
        try:
            out = o.read().decode().strip()
            print(f"  Result: {out[:200]}")
        except Exception:
            print("  (timeout - may still be running)")
        break

sftp.close()
ssh.close()
print("\nHecho! Revisa Telegram ahora.")
