"""Individual SSH commands to test each thing separately"""
import json
from shared_config import get_ssh_client, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

ssh = get_ssh_client()

BOT = TELEGRAM_BOT_TOKEN
CHAT_ID = TELEGRAM_CHAT_ID

# Test 1: Direct curl from HOST to Telegram
print("TEST 1: Curl from Hetzner host")
_, o, e = ssh.exec_command(
    f'curl -s -X POST "https://api.telegram.org/bot{BOT}/sendMessage"'
    ' -H "Content-Type: application/json"'
    f" -d '{{\"chat_id\": {CHAT_ID},"
    ' "text": "Test desde Hetzner host"}}\''
)
print(f"  {o.read().decode().strip()[:300]}")

# Test 2: Does n8n container have curl?
print("\nTEST 2: Check if n8n container has curl/wget")
_, o, _ = ssh.exec_command("docker exec n8n-n8n-1 which curl 2>/dev/null || echo NO_CURL")
print(f"  curl: {o.read().decode().strip()}")
_, o, _ = ssh.exec_command("docker exec n8n-n8n-1 which wget 2>/dev/null || echo NO_WGET")
print(f"  wget: {o.read().decode().strip()}")

# Test 3: Can n8n container reach internet?
print("\nTEST 3: n8n container internet access")
_, o, _ = ssh.exec_command(
    "docker exec n8n-n8n-1 node -e"
    " \"fetch('https://api.telegram.org/bot"
    + BOT
    + "/getMe').then(r=>r.json())"
    ".then(d=>console.log(JSON.stringify(d)))\""
    " 2>&1"
)
print(f"  {o.read().decode().strip()[:300]}")

# Test 4: Check what the actual Telegram credential contains
print("\nTEST 4: Telegram credential details")
_, o, _ = ssh.exec_command("docker exec n8n-n8n-1 n8n export:credentials --all --decrypted 2>&1")
raw = o.read().decode().strip()
try:
    all_creds = json.loads(raw)
    for c in all_creds:
        if "telegram" in c.get("type", "").lower():
            print(f"  Name: {c.get('name')}")
            print(f"  ID: {c.get('id')}")
            print(f"  Type: {c.get('type')}")
            print(f"  Data: {json.dumps(c.get('data', {}))}")
except Exception:
    print(f"  Could not parse (may need --decrypted support): {raw[:200]}")

# Test 5: What chatId does the workflow actually have?
print("\nTEST 5: Actual chatId in workflows")
_, o, _ = ssh.exec_command("docker exec n8n-n8n-1 n8n export:workflow --all")
wfs = json.loads(o.read().decode().strip())
for wf in wfs:
    for n in wf.get("nodes", []):
        chat = n.get("parameters", {}).get("chatId", "")
        if chat:
            print(f"  {wf['name']}/{n['name']}: chatId={chat}")

ssh.close()
print("\nDone!")
