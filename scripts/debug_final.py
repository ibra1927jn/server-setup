"""Debug final: revisar logs, execution history, y enviar test directo"""
import json, requests
from shared_config import get_ssh_client, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

ssh = get_ssh_client()

# 1. N8N logs
print("=== N8N LOGS (errores) ===")
_, o, _ = ssh.exec_command("docker logs n8n-n8n-1 --tail 80 2>&1")
logs = o.read().decode().strip()
for line in logs.split("\n"):
    low = line.lower()
    if any(k in low for k in ["error", "fail", "cred", "telegram", "warn", "unrecog"]):
        print(f"  {line.strip()[:150]}")

# 2. Check workflow execution errors more carefully
print("\n=== CHECK WORKFLOWS DETALLADO ===")
_, o, _ = ssh.exec_command("docker exec n8n-n8n-1 n8n export:workflow --all")
wfs = json.loads(o.read().decode().strip())
for wf in wfs:
    name = wf.get("name", "")
    active = wf.get("active", False)
    nodes = wf.get("nodes", [])
    node_info = []
    for n in nodes:
        ntype = n["type"].split(".")[-1]
        chatid = n.get("parameters", {}).get("chatId", "")
        cred = list(n.get("credentials", {}).keys())
        info = f"{n['name']}({ntype})"
        if chatid:
            info += f"[chat:{chatid}]"
        if cred:
            info += f"[creds:{cred}]"
        node_info.append(info)
    print(f"  {'OK' if active else 'XX'} {name}: {' -> '.join(node_info)}")

# 3. Test directo
print("\n=== TEST DIRECTO TELEGRAM ===")
r = requests.post(
    f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
    json={"chat_id": TELEGRAM_CHAT_ID, "text": "Test directo - si ves esto, Telegram funciona OK"}
)
print(f"  Status: {r.status_code}")
print(f"  Response: {r.text[:300]}")

ssh.close()
