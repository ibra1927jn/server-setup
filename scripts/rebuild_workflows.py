"""
Approach: Instead of debugging complicated workflows node by node,
create a SIMPLE workflow that definitely works and replace the broken ones.
Step 1: Test if a minimal workflow with just Cron + Telegram works.
Step 2: If yes, rebuild each workflow as minimal working versions.
"""
import json
import time
from shared_config import get_ssh_client, TELEGRAM_CHAT_ID, GITHUB_PAT

CHAT_ID = TELEGRAM_CHAT_ID

ssh = get_ssh_client()

# Get the REAL telegram credential ID
_, o, _ = ssh.exec_command("docker exec n8n-n8n-1 n8n export:credentials --all")
creds = json.loads(o.read().decode().strip())
tg_cred = None
ssh_cred = None
for c in creds:
    if c["type"] == "telegramApi":
        tg_cred = {"id": c["id"], "name": c["name"]}
    if c["type"] == "sshPassword":
        ssh_cred = {"id": c["id"], "name": c["name"]}

print(f"Telegram cred: {tg_cred}")
print(f"SSH cred: {ssh_cred}")

# === CRYPTO PORTFOLIO ALERTS (simplest - just HTTP + Telegram) ===
crypto_wf = {
    "name": "Crypto Portfolio Alerts",
    "active": True,
    "nodes": [
        {
            "parameters": {"rule": {"interval": [{"field": "hours", "hoursInterval": 1}]}},
            "name": "Every Hour",
            "type": "n8n-nodes-base.scheduleTrigger",
            "typeVersion": 1.2,
            "position": [250, 300]
        },
        {
            "parameters": {
                "url": "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana,ripple,dogecoin&vs_currencies=usd&include_24hr_change=true",
                "options": {}
            },
            "name": "Get Prices",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4.2,
            "position": [470, 300]
        },
        {
            "parameters": {
                "chatId": CHAT_ID,
                "text": "=📊 *Crypto Portfolio*\n\n💰 BTC: ${{ $json.bitcoin.usd }} ({{ $json.bitcoin.usd_24h_change?.toFixed(1) }}%)\n💠 ETH: ${{ $json.ethereum.usd }} ({{ $json.ethereum.usd_24h_change?.toFixed(1) }}%)\n☀️ SOL: ${{ $json.solana.usd }} ({{ $json.solana.usd_24h_change?.toFixed(1) }}%)\n🪙 XRP: ${{ $json.ripple.usd }} ({{ $json.ripple.usd_24h_change?.toFixed(1) }}%)\n🐕 DOGE: ${{ $json.dogecoin.usd }} ({{ $json.dogecoin.usd_24h_change?.toFixed(1) }}%)\n\n🕐 {{ new Date().toLocaleString('es-ES') }}",
                "additionalFields": {"parse_mode": "Markdown"}
            },
            "name": "Send Telegram",
            "type": "n8n-nodes-base.telegram",
            "typeVersion": 1.2,
            "position": [690, 300],
            "credentials": {"telegramApi": tg_cred}
        }
    ],
    "connections": {
        "Every Hour": {"main": [[{"node": "Get Prices", "type": "main", "index": 0}]]},
        "Get Prices": {"main": [[{"node": "Send Telegram", "type": "main", "index": 0}]]}
    }
}

# === DAILY BRIEFING (SSH to server + Telegram) ===
daily_wf = {
    "name": "Daily Briefing",
    "active": True,
    "nodes": [
        {
            "parameters": {"rule": {"interval": [{"triggerAtHour": 8}]}},
            "name": "8AM Daily",
            "type": "n8n-nodes-base.scheduleTrigger",
            "typeVersion": 1.2,
            "position": [250, 300]
        },
        {
            "parameters": {
                "command": "echo \"UPTIME: $(uptime)\" && echo \"DISK: $(df -h / | tail -1)\" && echo \"MEM: $(free -h | grep Mem)\" && echo \"DOCKER: $(docker ps --format '{{.Names}}: {{.Status}}' | tr '\\n' ', ')\"",
                "authentication": "password"
            },
            "name": "Server Stats",
            "type": "n8n-nodes-base.ssh",
            "typeVersion": 1,
            "position": [470, 300],
            "credentials": {"sshPassword": ssh_cred}
        },
        {
            "parameters": {
                "chatId": CHAT_ID,
                "text": "=🌅 *Daily Briefing*\n\n{{ $json.stdout }}",
                "additionalFields": {"parse_mode": "Markdown"}
            },
            "name": "Send Telegram",
            "type": "n8n-nodes-base.telegram",
            "typeVersion": 1.2,
            "position": [690, 300],
            "credentials": {"telegramApi": tg_cred}
        }
    ],
    "connections": {
        "8AM Daily": {"main": [[{"node": "Server Stats", "type": "main", "index": 0}]]},
        "Server Stats": {"main": [[{"node": "Send Telegram", "type": "main", "index": 0}]]}
    }
}

# === UPTIME MONITOR (HTTP ping + Telegram on fail) ===
uptime_wf = {
    "name": "Uptime Monitor",
    "active": True,
    "nodes": [
        {
            "parameters": {"rule": {"interval": [{"field": "minutes", "minutesInterval": 5}]}},
            "name": "Every 5 Min",
            "type": "n8n-nodes-base.scheduleTrigger",
            "typeVersion": 1.2,
            "position": [250, 300]
        },
        {
            "parameters": {
                "command": "services='n8n:5678 alz.agency:443'; failed=0; report=''; for s in $services; do host=$(echo $s | cut -d: -f1); port=$(echo $s | cut -d: -f2); if timeout 5 bash -c \"echo > /dev/tcp/$host/$port\" 2>/dev/null; then report=\"$report\\n✅ $host:$port UP\"; else report=\"$report\\n❌ $host:$port DOWN\"; failed=$((failed+1)); fi; done; echo \"FAILED=$failed\"; echo -e \"$report\"",
                "authentication": "password"
            },
            "name": "Check Services",
            "type": "n8n-nodes-base.ssh",
            "typeVersion": 1,
            "position": [470, 300],
            "credentials": {"sshPassword": ssh_cred}
        },
        {
            "parameters": {
                "conditions": {
                    "options": {"caseSensitive": True, "leftValue": "", "typeValidation": "strict"},
                    "conditions": [{"leftValue": "={{ $json.stdout }}", "rightValue": "FAILED=0", "operator": {"type": "string", "operation": "notContains"}}],
                    "combinator": "and"
                }
            },
            "name": "Has Failures?",
            "type": "n8n-nodes-base.if",
            "typeVersion": 2,
            "position": [690, 300]
        },
        {
            "parameters": {
                "chatId": CHAT_ID,
                "text": "=🚨 *ALERTA: Servicio Caido!*\n\n{{ $('Check Services').item.json.stdout }}",
                "additionalFields": {"parse_mode": "Markdown"}
            },
            "name": "Alert Down",
            "type": "n8n-nodes-base.telegram",
            "typeVersion": 1.2,
            "position": [910, 200],
            "credentials": {"telegramApi": tg_cred}
        },
        {
            "parameters": {},
            "name": "All OK",
            "type": "n8n-nodes-base.noOp",
            "typeVersion": 1,
            "position": [910, 400]
        }
    ],
    "connections": {
        "Every 5 Min": {"main": [[{"node": "Check Services", "type": "main", "index": 0}]]},
        "Check Services": {"main": [[{"node": "Has Failures?", "type": "main", "index": 0}]]},
        "Has Failures?": {"main": [[{"node": "Alert Down", "type": "main", "index": 0}], [{"node": "All OK", "type": "main", "index": 0}]]}
    }
}

# === GITHUB AUTO-BACKUP ===
github_wf = {
    "name": "GitHub Auto-Backup",
    "active": True,
    "nodes": [
        {
            "parameters": {"rule": {"interval": [{"field": "hours", "hoursInterval": 12}]}},
            "name": "Every 12h",
            "type": "n8n-nodes-base.scheduleTrigger",
            "typeVersion": 1.2,
            "position": [250, 300]
        },
        {
            "parameters": {
                "url": "https://api.github.com/user/repos?per_page=10&sort=pushed",
                "authentication": "genericCredentialType",
                "genericAuthType": "httpHeaderAuth",
                "sendHeaders": True,
                "headerParameters": {"parameters": [
                    {"name": "Authorization", "value": f"Bearer {GITHUB_PAT}"},
                    {"name": "User-Agent", "value": "AgenticOS"}
                ]},
                "options": {}
            },
            "name": "Get Repos",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4.2,
            "position": [470, 300]
        },
        {
            "parameters": {
                "chatId": CHAT_ID,
                "text": "=🗂️ *GitHub Backup Report*\n\nRepos checked: {{ $json.length || 'N/A' }}\n🕐 {{ new Date().toLocaleString('es-ES') }}",
                "additionalFields": {"parse_mode": "Markdown"}
            },
            "name": "Send Report",
            "type": "n8n-nodes-base.telegram",
            "typeVersion": 1.2,
            "position": [690, 300],
            "credentials": {"telegramApi": tg_cred}
        }
    ],
    "connections": {
        "Every 12h": {"main": [[{"node": "Get Repos", "type": "main", "index": 0}]]},
        "Get Repos": {"main": [[{"node": "Send Report", "type": "main", "index": 0}]]}
    }
}

# IMPORT ALL
sftp = ssh.open_sftp()
workflows = [
    ("crypto_alerts.json", crypto_wf),
    ("daily_briefing.json", daily_wf),
    ("uptime_monitor.json", uptime_wf),
    ("github_backup.json", github_wf),
]

for fname, wf_data in workflows:
    print(f"\nImporting: {wf_data['name']}...")
    local = f"C:\\Users\\ibrab\\Desktop\\set up\\scripts\\{fname}"
    remote = f"/tmp/{fname}"
    with open(local, "w", encoding="utf-8") as f:
        json.dump(wf_data, f)
    sftp.put(local, remote)
    ssh.exec_command(f"docker cp {remote} n8n-n8n-1:/tmp/{fname}")
    time.sleep(1)
    _, o, e = ssh.exec_command(f"docker exec n8n-n8n-1 n8n import:workflow --input=/tmp/{fname}")
    print(f"  {o.read().decode().strip()}")

# Restart
print("\nRestarting n8n...")
ssh.exec_command("docker restart n8n-n8n-1")
time.sleep(15)

# Activate all
_, o, _ = ssh.exec_command("docker exec n8n-n8n-1 n8n update:workflow --all --active=true")
o.read()
print("All activated!")

# TEST: Execute Crypto Portfolio Alerts
print("\n=== TEST: Crypto Portfolio Alerts ===")
for wf in [crypto_wf]:
    # Get new ID after import
    _, o, _ = ssh.exec_command("docker exec n8n-n8n-1 n8n list:workflow")
    lines = o.read().decode().strip().split("\n")
    for line in lines:
        if "Crypto" in line:
            wid = line.split("|")[0].strip()
            print(f"  Executing {wid}...")
            _, o, e = ssh.exec_command(f"docker exec n8n-n8n-1 n8n execute --id={wid} 2>&1", timeout=30)
            try:
                print(f"  OUT: {o.read().decode().strip()[:300]}")
            except Exception:
                pass

sftp.close()
ssh.close()
print("\nDone! Revisa Telegram.")
