"""
Approach final: Usar la REST API interna de n8n para actualizar
los workflows existentes con los nodos correctos.
"""
import json
import time

from shared_config import GITHUB_PAT, TELEGRAM_CHAT_ID, VPS_HOST, get_ssh_client


def fetch_credentials(ssh):
    """Fetch telegram and SSH credential IDs from n8n."""
    _, o, _ = ssh.exec_command("docker exec n8n-n8n-1 n8n export:credentials --all")
    creds = json.loads(o.read().decode().strip())
    tg_cred = None
    ssh_cred = None
    for c in creds:
        if c["type"] == "telegramApi":
            tg_cred = {"id": c["id"], "name": c["name"]}
        if c["type"] == "sshPassword":
            ssh_cred = {"id": c["id"], "name": c["name"]}
    return tg_cred, ssh_cred


def fetch_workflow_ids(ssh):
    """Fetch existing workflow name-to-ID mapping from n8n."""
    _, o, _ = ssh.exec_command("docker exec n8n-n8n-1 n8n export:workflow --all")
    existing = json.loads(o.read().decode().strip())
    wf_ids = {}
    for wf in existing:
        wf_ids[wf["name"]] = wf["id"]
        print(f"  {wf['name']} -> {wf['id']}")
    return wf_ids


def build_crypto_workflow(wf_id, chat_id, tg_cred):
    """Build the Crypto Portfolio Alerts workflow definition."""
    return {
        "id": wf_id,
        "name": "Crypto Portfolio Alerts",
        "active": True,
        "nodes": [
            {
                "parameters": {"rule": {"interval": [{"field": "hours", "hoursInterval": 1}]}},
                "name": "Every Hour",
                "type": "n8n-nodes-base.scheduleTrigger",
                "typeVersion": 1.2,
                "position": [250, 300],
                "id": "node1"
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
                "name": "Get Prices",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.2,
                "position": [470, 300],
                "id": "node2"
            },
            {
                "parameters": {
                    "chatId": chat_id,
                    "text": (
                        "=📊 *Crypto Portfolio*\n\n"
                        "💰 BTC: ${{ $json.bitcoin.usd }} "
                        "({{ $json.bitcoin.usd_24h_change.toFixed(1) }}%)\n"
                        "💠 ETH: ${{ $json.ethereum.usd }} "
                        "({{ $json.ethereum.usd_24h_change.toFixed(1) }}%)\n"
                        "☀️ SOL: ${{ $json.solana.usd }} "
                        "({{ $json.solana.usd_24h_change.toFixed(1) }}%)\n"
                        "🪙 XRP: ${{ $json.ripple.usd }} "
                        "({{ $json.ripple.usd_24h_change.toFixed(1) }}%)\n"
                        "🐕 DOGE: ${{ $json.dogecoin.usd }} "
                        "({{ $json.dogecoin.usd_24h_change.toFixed(1) }}%)"
                    ),
                    "additionalFields": {"parse_mode": "Markdown"}
                },
                "name": "Send Telegram",
                "type": "n8n-nodes-base.telegram",
                "typeVersion": 1.2,
                "position": [690, 300],
                "id": "node3",
                "credentials": {"telegramApi": tg_cred}
            }
        ],
        "connections": {
            "Every Hour": {"main": [[{"node": "Get Prices", "type": "main", "index": 0}]]},
            "Get Prices": {"main": [[{"node": "Send Telegram", "type": "main", "index": 0}]]}
        }
    }


def build_daily_workflow(wf_id, chat_id, ssh_cred, tg_cred):
    """Build the Daily Briefing workflow definition."""
    return {
        "id": wf_id,
        "name": "Daily Briefing",
        "active": True,
        "nodes": [
            {
                "parameters": {"rule": {"interval": [{"triggerAtHour": 8}]}},
                "name": "8AM Daily",
                "type": "n8n-nodes-base.scheduleTrigger",
                "typeVersion": 1.2,
                "position": [250, 300],
                "id": "node1"
            },
            {
                "parameters": {
                    "command": (
                        "uptime && df -h / | tail -1"
                        " && free -h | grep Mem"
                        " && docker ps --format"
                        " '{{.Names}}: {{.Status}}'"
                    ),
                    "authentication": "password"
                },
                "name": "Server Stats",
                "type": "n8n-nodes-base.ssh",
                "typeVersion": 1,
                "position": [470, 300],
                "id": "node2",
                "credentials": {"sshPassword": ssh_cred}
            },
            {
                "parameters": {
                    "chatId": chat_id,
                    "text": "=🌅 *Daily Briefing*\n\n{{ $json.stdout }}",
                    "additionalFields": {"parse_mode": "Markdown"}
                },
                "name": "Send Telegram",
                "type": "n8n-nodes-base.telegram",
                "typeVersion": 1.2,
                "position": [690, 300],
                "id": "node3",
                "credentials": {"telegramApi": tg_cred}
            }
        ],
        "connections": {
            "8AM Daily": {"main": [[{"node": "Server Stats", "type": "main", "index": 0}]]},
            "Server Stats": {"main": [[{"node": "Send Telegram", "type": "main", "index": 0}]]}
        }
    }


def build_uptime_workflow(wf_id):
    """Build the Uptime Monitor workflow definition."""
    return {
        "id": wf_id,
        "name": "Uptime Monitor",
        "active": True,
        "nodes": [
            {
                "parameters": {"rule": {"interval": [{"field": "minutes", "minutesInterval": 5}]}},
                "name": "Every 5 Min",
                "type": "n8n-nodes-base.scheduleTrigger",
                "typeVersion": 1.2,
                "position": [250, 300],
                "id": "node1"
            },
            {
                "parameters": {
                    "url": f"http://{VPS_HOST}:5678/healthz",
                    "options": {"timeout": 5000}
                },
                "name": "Ping n8n",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.2,
                "position": [470, 300],
                "id": "node2",
                "onError": "continueRegularOutput"
            },
            {
                "parameters": {},
                "name": "All OK",
                "type": "n8n-nodes-base.noOp",
                "typeVersion": 1,
                "position": [690, 300],
                "id": "node3"
            }
        ],
        "connections": {
            "Every 5 Min": {"main": [[{"node": "Ping n8n", "type": "main", "index": 0}]]},
            "Ping n8n": {"main": [[{"node": "All OK", "type": "main", "index": 0}]]}
        }
    }


def build_github_workflow(wf_id, chat_id, tg_cred):
    """Build the GitHub Auto-Backup workflow definition."""
    return {
        "id": wf_id,
        "name": "GitHub Auto-Backup",
        "active": True,
        "nodes": [
            {
                "parameters": {"rule": {"interval": [{"field": "hours", "hoursInterval": 12}]}},
                "name": "Every 12h",
                "type": "n8n-nodes-base.scheduleTrigger",
                "typeVersion": 1.2,
                "position": [250, 300],
                "id": "node1"
            },
            {
                "parameters": {
                    "url": "https://api.github.com/user/repos?per_page=5&sort=pushed",
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
                "position": [470, 300],
                "id": "node2"
            },
            {
                "parameters": {
                    "chatId": chat_id,
                    "text": (
                        "=🗂️ *GitHub Backup Report*\n\n"
                        "Repos recientes revisados\n"
                        "🕐 {{ new Date().toLocaleString('es-ES') }}"
                    ),
                    "additionalFields": {"parse_mode": "Markdown"}
                },
                "name": "Send Report",
                "type": "n8n-nodes-base.telegram",
                "typeVersion": 1.2,
                "position": [690, 300],
                "id": "node3",
                "credentials": {"telegramApi": tg_cred}
            }
        ],
        "connections": {
            "Every 12h": {"main": [[{"node": "Get Repos", "type": "main", "index": 0}]]},
            "Get Repos": {"main": [[{"node": "Send Report", "type": "main", "index": 0}]]}
        }
    }


def import_and_deploy_workflows(ssh, workflows):
    """Import workflows to n8n via SFTP, restart, and activate all."""
    sftp = ssh.open_sftp()
    for name, wf_data in workflows.items():
        print(f"\nUpdating: {name} (ID: {wf_data['id']})...")
        fname = f"update_{name.lower().replace(' ', '_')}.json"
        local = f"C:\\Users\\ibrab\\Desktop\\set up\\scripts\\{fname}"
        remote = f"/tmp/{fname}"
        with open(local, "w", encoding="utf-8") as f:
            json.dump(wf_data, f)
        sftp.put(local, remote)
        ssh.exec_command(f"docker cp {remote} n8n-n8n-1:/tmp/{fname}")
        time.sleep(1)
        _, o, e = ssh.exec_command(f"docker exec n8n-n8n-1 n8n import:workflow --input=/tmp/{fname}")
        out = o.read().decode().strip()
        err = e.read().decode().strip()
        print(f"  OUT: {out[:100]}")
        if err:
            print(f"  ERR: {err[:100]}")

    print("\nRestarting...")
    ssh.exec_command("docker restart n8n-n8n-1")
    time.sleep(15)

    _, o, _ = ssh.exec_command("docker exec n8n-n8n-1 n8n update:workflow --all --active=true")
    o.read()

    sftp.close()


def test_crypto_workflow(ssh):
    """Execute the Crypto Portfolio Alerts workflow as a smoke test."""
    print("\n=== TEST FINAL: Crypto Portfolio Alerts ===")
    _, o, _ = ssh.exec_command("docker exec n8n-n8n-1 n8n list:workflow")
    for line in o.read().decode().strip().split("\n"):
        if "Crypto" in line:
            wid = line.split("|")[0].strip()
            print(f"  Executing {wid}...")
            _, o2, e2 = ssh.exec_command(f"docker exec n8n-n8n-1 n8n execute --id={wid} 2>&1", timeout=30)
            try:
                full = o2.read().decode().strip()
                print(f"  FULL OUTPUT:\n{full}")
            except Exception:
                print("  timeout")


def main():
    chat_id = TELEGRAM_CHAT_ID
    ssh = get_ssh_client()

    tg_cred, ssh_cred = fetch_credentials(ssh)
    print(f"TG: {tg_cred}")
    print(f"SSH: {ssh_cred}")

    wf_ids = fetch_workflow_ids(ssh)

    workflows = {}
    if "Crypto Portfolio Alerts" in wf_ids:
        workflows["Crypto Portfolio Alerts"] = build_crypto_workflow(
            wf_ids["Crypto Portfolio Alerts"], chat_id, tg_cred
        )
    if "Daily Briefing" in wf_ids:
        workflows["Daily Briefing"] = build_daily_workflow(
            wf_ids["Daily Briefing"], chat_id, ssh_cred, tg_cred
        )
    if "Uptime Monitor" in wf_ids:
        workflows["Uptime Monitor"] = build_uptime_workflow(
            wf_ids["Uptime Monitor"]
        )
    if "GitHub Auto-Backup" in wf_ids:
        workflows["GitHub Auto-Backup"] = build_github_workflow(
            wf_ids["GitHub Auto-Backup"], chat_id, tg_cred
        )

    import_and_deploy_workflows(ssh, workflows)
    test_crypto_workflow(ssh)

    ssh.close()
    print("\nDone! Check Telegram.")


if __name__ == "__main__":
    main()
