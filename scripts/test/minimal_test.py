"""
Minimal absolute test:
1. Create workflow with ONLY a manual trigger + telegram with plain text
2. Execute it
3. Check if message arrives
"""
import json
from shared_config import get_ssh_client, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

BOT = TELEGRAM_BOT_TOKEN
CHAT_ID = TELEGRAM_CHAT_ID

ssh = get_ssh_client()

# Get cred
_, o, _ = ssh.exec_command("docker exec n8n-n8n-1 n8n export:credentials --all")
creds = json.loads(o.read().decode().strip())
tg_cred = None
for c in creds:
    if c["type"] == "telegramApi":
        tg_cred = {"id": c["id"], "name": c["name"]}
        break
print(f"TG Cred: {tg_cred}")

# Step 1: Try sending directly from the server via curl
print("\n=== STEP 1: Direct curl from server ===")
cmd = (
    f'curl -s -X POST "https://api.telegram.org/bot{BOT}/sendMessage"'
    f' -H "Content-Type: application/json"'
    f' -d \'{{"chat_id": {CHAT_ID},'
    f' "text": "Direct from Hetzner server via curl"}}\''
)
_, o, e = ssh.exec_command(cmd)
result = o.read().decode().strip()
print(f"  Result: {result[:300]}")

# Step 2: Execute the simplest possible workflow - just the CoinGecko one
print("\n=== STEP 2: Try HTTP request to CoinGecko from server ===")
cmd2 = 'curl -s "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd" 2>&1'
_, o, _ = ssh.exec_command(cmd2)
print(f"  CoinGecko: {o.read().decode().strip()}")

# Step 3: Check if n8n can resolve DNS
print("\n=== STEP 3: DNS from n8n container ===")
n8n_tg_cmd = (
    'docker exec n8n-n8n-1 sh -c "wget -q -O-'
    ' https://api.telegram.org/bot{BOT}/getMe 2>&1'
    ' || curl -s https://api.telegram.org/bot{BOT}/getMe 2>&1'
    ' || echo NO_CURL_NO_WGET"'
).replace("{BOT}", BOT)
_, o, _ = ssh.exec_command(n8n_tg_cmd)
print(f"  n8n container telegram: {o.read().decode().strip()[:200]}")

# Step 4: Check workflow execution from the DB
print("\n=== STEP 4: Recent executions from DB ===")
db_cmd = """docker exec n8n-n8n-1 sh -c 'node -e "
const sqlite3 = require(\\\"better-sqlite3\\\");
try {
  const db = new sqlite3(\\\"/home/node/.n8n/database.sqlite\\\");
  const q = \\\"SELECT id, workflowId, finished, mode, status FROM execution_entity ORDER BY id DESC LIMIT 8\\\";
  const rows = db.prepare(q).all();
  console.log(JSON.stringify(rows, null, 2));
} catch(e) { console.log(e.message); }
"'"""
_, o, _ = ssh.exec_command(db_cmd)
print(f"  DB: {o.read().decode().strip()[:500]}")

ssh.close()
print("\nDone!")
