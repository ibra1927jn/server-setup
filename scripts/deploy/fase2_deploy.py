"""
Fase 2 — Paso 1: Configurar Firewall en Hetzner
Paso 2: Crear e importar los 4 workflows avanzados
"""
import json
import time
import random
import string
from shared_config import get_ssh_client, N8N_CRED_SSH, N8N_CRED_TELEGRAM_BOT

ssh = get_ssh_client()

# =====================================================
# PASO 1: FIREWALL
# =====================================================
print("=" * 60)
print("PASO 1: CONFIGURANDO FIREWALL")
print("=" * 60)

firewall_commands = [
    # Reset UFW
    "apt-get install -y ufw",
    # Default policies
    "ufw default deny incoming",
    "ufw default allow outgoing",
    # Allow SSH
    "ufw allow 22/tcp comment 'SSH'",
    # Allow n8n
    "ufw allow 5678/tcp comment 'n8n'",
    # Allow HTTP/HTTPS (para futuro Nginx)
    "ufw allow 80/tcp comment 'HTTP'",
    "ufw allow 443/tcp comment 'HTTPS'",
    # Enable
    "echo 'y' | ufw enable",
    # Status
    "ufw status verbose",
]

for cmd in firewall_commands:
    print(f"\n>>> {cmd}")
    _, o, e = ssh.exec_command(cmd)
    out = o.read().decode().strip()
    err = e.read().decode().strip()
    if out:
        print(out)
    if err and 'WARNING' not in err:
        print(f"  ERR: {err}")

print("\n✅ Firewall configurado!")

# =====================================================
# PASO 2: CREAR WORKFLOWS AVANZADOS
# =====================================================
print("\n" + "=" * 60)
print("PASO 2: CREANDO WORKFLOWS AVANZADOS")
print("=" * 60)


def gen_id():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=16))


# --- WORKFLOW 1: Daily Briefing ---
daily_briefing = {
    "id": gen_id(),
    "name": "Daily Briefing",
    "nodes": [
        {
            "parameters": {
                "rule": {"interval": [{"triggerAtHour": 8}]}
            },
            "id": gen_id(),
            "name": "Cron 8AM",
            "type": "n8n-nodes-base.scheduleTrigger",
            "typeVersion": 1.2,
            "position": [250, 300]
        },
        {
            "parameters": {
                "command": (
                    "echo '=== SERVER STATUS ===' && uptime && echo ''"
                    " && echo '=== DISK ===' && df -h / | tail -1"
                    " && echo '' && echo '=== MEMORY ===' && free -m"
                    " | grep Mem && echo '' && echo '=== DOCKER ==='"
                    " && docker ps --format 'table {{.Names}}\t{{.Status}}'"
                    " && echo '' && echo '=== N8N WORKFLOWS ==='"
                    " && docker exec n8n-n8n-1 n8n list:workflow"
                    " 2>/dev/null || echo 'n8n CLI unavailable'"
                )
            },
            "id": gen_id(),
            "name": "Check Server",
            "type": "n8n-nodes-base.executeCommand",
            "typeVersion": 1,
            "position": [470, 300],
            "credentials": {
                "sshPassword": {
                    "id": N8N_CRED_SSH,
                    "name": "Hetzner Root SSH"
                }
            }
        },
        {
            "parameters": {
                "chatId": "6915862027",
                "text": (
                    "=🌅 **DAILY BRIEFING — AgenticOS**\n"
                    "📅 {{ $now.format('dd/MM/yyyy HH:mm') }}"
                    "\n\n{{ $json.stdout }}"
                ),
                "additionalFields": {"parse_mode": "Markdown"}
            },
            "id": gen_id(),
            "name": "Telegram Briefing",
            "type": "n8n-nodes-base.telegram",
            "typeVersion": 1.2,
            "position": [690, 300],
            "credentials": {
                "telegramApi": {
                    "id": N8N_CRED_TELEGRAM_BOT,
                    "name": "AgenticOS Bot"
                }
            }
        }
    ],
    "connections": {
        "Cron 8AM": {"main": [[{"node": "Check Server", "type": "main", "index": 0}]]},
        "Check Server": {"main": [[{"node": "Telegram Briefing", "type": "main", "index": 0}]]}
    },
    "active": True,
    "settings": {"executionOrder": "v1"},
    "meta": {"templateCredsSetupCompleted": True}
}

# --- WORKFLOW 2: Uptime Monitor ---
uptime_monitor = {
    "id": gen_id(),
    "name": "Uptime Monitor",
    "nodes": [
        {
            "parameters": {
                "rule": {"interval": [{"field": "minutes", "minutesInterval": 5}]}
            },
            "id": gen_id(),
            "name": "Every 5min",
            "type": "n8n-nodes-base.scheduleTrigger",
            "typeVersion": 1.2,
            "position": [250, 300]
        },
        {
            "parameters": {
                "command": (
                    "services='95.217.158.7:5678 alz.agency'\n"
                    "result=''\nfailed=0\n"
                    "for svc in $services; do\n"
                    "  host=$(echo $svc | cut -d: -f1)\n"
                    "  port=$(echo $svc | cut -d: -f2)\n"
                    "  if [ -z \"$port\" ]; then port=443; fi\n"
                    "  if timeout 5 bash -c "
                    "\"echo > /dev/tcp/$host/$port\""
                    " 2>/dev/null; then\n"
                    "    result=\"$result\\n✅ $svc — UP\"\n"
                    "  else\n"
                    "    result=\"$result\\n❌ $svc — DOWN!\"\n"
                    "    failed=$((failed+1))\n"
                    "  fi\ndone\n"
                    "echo -e \"$result\"\n"
                    "echo \"FAILED=$failed\""
                )
            },
            "id": gen_id(),
            "name": "Ping Services",
            "type": "n8n-nodes-base.executeCommand",
            "typeVersion": 1,
            "position": [470, 300],
            "credentials": {
                "sshPassword": {
                    "id": N8N_CRED_SSH,
                    "name": "Hetzner Root SSH"
                }
            }
        },
        {
            "parameters": {
                "conditions": {
                    "options": {"caseSensitive": True, "leftValue": "", "typeValidation": "strict"},
                    "conditions": [
                        {
                            "id": gen_id(),
                            "leftValue": "={{ $json.stdout }}",
                            "rightValue": "FAILED=0",
                            "operator": {"type": "string", "operation": "notContains"}
                        }
                    ]
                }
            },
            "id": gen_id(),
            "name": "Any Failed?",
            "type": "n8n-nodes-base.if",
            "typeVersion": 2,
            "position": [690, 300]
        },
        {
            "parameters": {
                "chatId": "6915862027",
                "text": (
                    "=🚨 **ALERTA UPTIME — AgenticOS**\n"
                    "⏰ {{ $now.format('HH:mm') }}\n\n"
                    "{{ $('Ping Services').item.json.stdout }}"
                ),
                "additionalFields": {"parse_mode": "Markdown"}
            },
            "id": gen_id(),
            "name": "Alert Telegram",
            "type": "n8n-nodes-base.telegram",
            "typeVersion": 1.2,
            "position": [910, 200],
            "credentials": {
                "telegramApi": {
                    "id": N8N_CRED_TELEGRAM_BOT,
                    "name": "AgenticOS Bot"
                }
            }
        },
        {
            "parameters": {},
            "id": gen_id(),
            "name": "All OK",
            "type": "n8n-nodes-base.noOp",
            "typeVersion": 1,
            "position": [910, 400]
        }
    ],
    "connections": {
        "Every 5min": {"main": [[{"node": "Ping Services", "type": "main", "index": 0}]]},
        "Ping Services": {"main": [[{"node": "Any Failed?", "type": "main", "index": 0}]]},
        "Any Failed?": {
            "main": [
                [{"node": "Alert Telegram", "type": "main", "index": 0}],
                [{"node": "All OK", "type": "main", "index": 0}]
            ]
        }
    },
    "active": True,
    "settings": {"executionOrder": "v1"},
    "meta": {"templateCredsSetupCompleted": True}
}

# --- WORKFLOW 3: Crypto Portfolio Alerts ---
crypto_alerts = {
    "id": gen_id(),
    "name": "Crypto Portfolio Alerts",
    "nodes": [
        {
            "parameters": {
                "rule": {"interval": [{"field": "hours", "hoursInterval": 1}]}
            },
            "id": gen_id(),
            "name": "Every 1h",
            "type": "n8n-nodes-base.scheduleTrigger",
            "typeVersion": 1.2,
            "position": [250, 300]
        },
        {
            "parameters": {
                "url": (
                    "https://api.coingecko.com/api/v3/simple/price"
                    "?ids=bitcoin,ethereum,solana,ripple,dogecoin"
                    "&vs_currencies=usd&include_24hr_change=true"
                ),
                "options": {}
            },
            "id": gen_id(),
            "name": "Get Prices",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4.2,
            "position": [470, 300]
        },
        {
            "parameters": {
                "jsCode": (
                    "const data = $input.first().json;\n"
                    "const alerts = [];\n"
                    "const coins = {\n"
                    "  'bitcoin': 'BTC',\n"
                    "  'ethereum': 'ETH',\n"
                    "  'solana': 'SOL',\n"
                    "  'ripple': 'XRP',\n"
                    "  'dogecoin': 'DOGE'\n"
                    "};\n\n"
                    "let report = '📊 **CRYPTO PORTFOLIO**\\n';\n"
                    "report += `⏰ "
                    "${new Date().toLocaleString('es-ES')}"
                    "\\n\\n`;\n\n"
                    "let hasAlert = false;\n"
                    "for (const [id, symbol] of "
                    "Object.entries(coins)) {\n"
                    "  if (data[id]) {\n"
                    "    const price = data[id].usd;\n"
                    "    const change = "
                    "data[id].usd_24h_change?.toFixed(2)"
                    " || '0';\n"
                    "    const emoji = "
                    "change >= 0 ? '🟢' : '🔴';\n"
                    "    const alertEmoji = "
                    "Math.abs(change) > 5 ? '⚠️' : '';\n"
                    "    report += `${emoji} "
                    "**${symbol}**: "
                    "$${price.toLocaleString()} "
                    "(${change > 0 ? '+' : ''}"
                    "${change}%) ${alertEmoji}\\n`;\n"
                    "    if (Math.abs(change) > 5) "
                    "hasAlert = true;\n"
                    "  }\n}\n\n"
                    "return [{ json: "
                    "{ report, hasAlert } }];"
                )
            },
            "id": gen_id(),
            "name": "Format Prices",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [690, 300]
        },
        {
            "parameters": {
                "chatId": "6915862027",
                "text": "={{ $json.report }}",
                "additionalFields": {"parse_mode": "Markdown"}
            },
            "id": gen_id(),
            "name": "Send Report",
            "type": "n8n-nodes-base.telegram",
            "typeVersion": 1.2,
            "position": [910, 300],
            "credentials": {
                "telegramApi": {
                    "id": N8N_CRED_TELEGRAM_BOT,
                    "name": "AgenticOS Bot"
                }
            }
        }
    ],
    "connections": {
        "Every 1h": {"main": [[{"node": "Get Prices", "type": "main", "index": 0}]]},
        "Get Prices": {"main": [[{"node": "Format Prices", "type": "main", "index": 0}]]},
        "Format Prices": {"main": [[{"node": "Send Report", "type": "main", "index": 0}]]}
    },
    "active": True,
    "settings": {"executionOrder": "v1"},
    "meta": {"templateCredsSetupCompleted": True}
}

# --- WORKFLOW 4: GitHub Auto-Backup ---
github_backup = {
    "id": gen_id(),
    "name": "GitHub Auto-Backup",
    "nodes": [
        {
            "parameters": {
                "rule": {"interval": [{"field": "hours", "hoursInterval": 12}]}
            },
            "id": gen_id(),
            "name": "Every 12h",
            "type": "n8n-nodes-base.scheduleTrigger",
            "typeVersion": 1.2,
            "position": [250, 300]
        },
        {
            "parameters": {
                "url": "https://api.github.com/user/repos?per_page=100&sort=pushed",
                "authentication": "genericCredentialType",
                "genericAuthType": "httpHeaderAuth",
                "options": {}
            },
            "id": gen_id(),
            "name": "Get Repos",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4.2,
            "position": [470, 300]
        },
        {
            "parameters": {
                "jsCode": (
                    "const repos = "
                    "$input.all().map(i => i.json);\n"
                    "const now = new Date();\n"
                    "const DAYS_THRESHOLD = 7;\n"
                    "let report = "
                    "'🗂️ **GITHUB BACKUP REPORT**\\n';\n"
                    "report += `⏰ "
                    "${now.toLocaleString('es-ES')}"
                    "\\n\\n`;\n\n"
                    "let inactive = [];\n"
                    "let total = 0;\n\n"
                    "for (const repo of repos) {\n"
                    "  if (repo.fork) continue;\n"
                    "  total++;\n"
                    "  const pushed = "
                    "new Date(repo.pushed_at);\n"
                    "  const daysSince = Math.floor("
                    "(now - pushed) / (1000*60*60*24));\n"
                    "  \n"
                    "  if (daysSince > DAYS_THRESHOLD) {\n"
                    "    inactive.push(`⚠️ "
                    "**${repo.name}** — "
                    "${daysSince}d sin actividad`);\n"
                    "  }\n}\n\n"
                    "report += `📦 Total repos propios: "
                    "${total}\\n`;\n"
                    "report += `✅ Activos "
                    "(< ${DAYS_THRESHOLD}d): "
                    "${total - inactive.length}\\n`;\n"
                    "report += `⚠️ Inactivos "
                    "(> ${DAYS_THRESHOLD}d): "
                    "${inactive.length}\\n\\n`;\n\n"
                    "if (inactive.length > 0) {\n"
                    "  report += "
                    "'**Repos inactivos:**\\n';\n"
                    "  report += "
                    "inactive.slice(0, 10).join('\\n');\n"
                    "  if (inactive.length > 10) "
                    "report += `\\n... y "
                    "${inactive.length - 10} más`;\n"
                    "}\n\n"
                    "return [{ json: { report, "
                    "inactiveCount: inactive.length } }];"
                )
            },
            "id": gen_id(),
            "name": "Analyze Repos",
            "type": "n8n-nodes-base.code",
            "typeVersion": 2,
            "position": [690, 300]
        },
        {
            "parameters": {
                "chatId": "6915862027",
                "text": "={{ $json.report }}",
                "additionalFields": {"parse_mode": "Markdown"}
            },
            "id": gen_id(),
            "name": "Send Report",
            "type": "n8n-nodes-base.telegram",
            "typeVersion": 1.2,
            "position": [910, 300],
            "credentials": {
                "telegramApi": {
                    "id": N8N_CRED_TELEGRAM_BOT,
                    "name": "AgenticOS Bot"
                }
            }
        }
    ],
    "connections": {
        "Every 12h": {"main": [[{"node": "Get Repos", "type": "main", "index": 0}]]},
        "Get Repos": {"main": [[{"node": "Analyze Repos", "type": "main", "index": 0}]]},
        "Analyze Repos": {"main": [[{"node": "Send Report", "type": "main", "index": 0}]]}
    },
    "active": True,
    "settings": {"executionOrder": "v1"},
    "meta": {"templateCredsSetupCompleted": True}
}

# =====================================================
# IMPORTAR TODOS LOS WORKFLOWS
# =====================================================
print("\n" + "=" * 60)
print("IMPORTANDO WORKFLOWS")
print("=" * 60)

sftp = ssh.open_sftp()
workflows = {
    "daily_briefing.json": daily_briefing,
    "uptime_monitor.json": uptime_monitor,
    "crypto_alerts.json": crypto_alerts,
    "github_backup.json": github_backup,
}

for filename, wf_data in workflows.items():
    print(f"\n--- {wf_data['name']} ---")
    local_path = f"C:\\Users\\ibrab\\Desktop\\set up\\scripts\\{filename}"
    remote_path = f"/tmp/n8n-import/{filename}"

    with open(local_path, 'w', encoding='utf-8') as f:
        json.dump(wf_data, f)

    sftp.put(local_path, remote_path)
    ssh.exec_command(f"docker cp {remote_path} n8n-n8n-1:/tmp/n8n-import/{filename}")
    time.sleep(1)

    _, o, e = ssh.exec_command(f"docker exec n8n-n8n-1 n8n import:workflow --input=/tmp/n8n-import/{filename}")
    out = o.read().decode().strip()
    err = e.read().decode().strip()
    print(f"  OUT: {out}")
    if 'error' in err.lower():
        print(f"  ERR: {err}")

# Activate all
print("\n--- Activando todos ---")
_, o, e = ssh.exec_command("docker exec n8n-n8n-1 n8n update:workflow --all --active=true")
out = o.read().decode().strip()
print(out)

# Restart to apply
print("\n--- Reiniciando n8n ---")
ssh.exec_command("docker restart n8n-n8n-1")
time.sleep(12)

# Final listing
print("\n" + "=" * 60)
print("ESTADO FINAL")
print("=" * 60)
_, o, _ = ssh.exec_command("docker exec n8n-n8n-1 n8n list:workflow")
print(o.read().decode().strip())

# Firewall status
print("\n--- FIREWALL ---")
_, o, _ = ssh.exec_command("ufw status")
print(o.read().decode().strip())

sftp.close()
ssh.close()
print("\n✅ FASE 2 DESPLEGADA!")
