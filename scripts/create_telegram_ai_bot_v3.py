import json
import time
import uuid
from shared_config import get_ssh_client, N8N_CRED_TELEGRAM, N8N_CRED_OPENROUTER

ssh = get_ssh_client()

wf_id = uuid.uuid4().hex[:16]

telegram_ai_workflow = {
    "id": wf_id,
    "name": "Telegram AI Bot",
    "active": False,
    "nodes": [
        {
            "parameters": {
                "updates": ["message"]
            },
            "type": "n8n-nodes-base.telegramTrigger",
            "typeVersion": 1.1,
            "position": [220, 300],
            "id": uuid.uuid4().hex[:8],
            "name": "Telegram Trigger",
            "credentials": {
                "telegramApi": {
                    "id": N8N_CRED_TELEGRAM,
                    "name": "Telegram account"
                }
            }
        },
        {
            "parameters": {
                "options": {
                    "systemMessage": (
                        "Eres un asistente de IA conciso llamado"
                        " AgenticOS. Responde en español. Sé"
                        " breve, máximo 2 párrafos."
                    )
                }
            },
            "type": "@n8n/n8n-nodes-langchain.agent",
            "typeVersion": 1.7,
            "position": [480, 300],
            "id": uuid.uuid4().hex[:8],
            "name": "AI Agent"
        },
        {
            "parameters": {
                "model": "zhipuai/glm-4.5-air",
                "options": {
                    "maxTokens": 500,
                    "temperature": 0.7
                }
            },
            "type": "@n8n/n8n-nodes-langchain.lmChatOpenAi",
            "typeVersion": 1.2,
            "position": [400, 520],
            "id": uuid.uuid4().hex[:8],
            "name": "GLM-4.5 Air",
            "credentials": {
                "openAiApi": {
                    "id": N8N_CRED_OPENROUTER,
                    "name": "OpenRouter Account"
                }
            }
        }
    ],
    "connections": {
        "Telegram Trigger": {
            "main": [
                [
                    {
                        "node": "AI Agent",
                        "type": "main",
                        "index": 0
                    }
                ]
            ]
        },
        "GLM-4.5 Air": {
            "ai_languageModel": [
                [
                    {
                        "node": "AI Agent",
                        "type": "ai_languageModel",
                        "index": 0
                    }
                ]
            ]
        }
    },
    "settings": {
        "executionOrder": "v1"
    }
}

workflow_json = json.dumps([telegram_ai_workflow])

with ssh.open_sftp() as sftp:
    with sftp.file('/tmp/telegram_ai_bot.json', 'w') as f:
        f.write(workflow_json)

time.sleep(1)

ssh.exec_command("docker cp /tmp/telegram_ai_bot.json n8n-n8n-1:/tmp/telegram_ai_bot.json")
time.sleep(1)

_, o, e = ssh.exec_command("docker exec n8n-n8n-1 n8n import:workflow --input=/tmp/telegram_ai_bot.json")
stdout = o.read().decode()
stderr = e.read().decode()
print("STDOUT:", stdout)
print("STDERR:", stderr)

if "error" not in stdout.lower():
    print(f"\nSUCCESS! Workflow ID: {wf_id}")
    print("Now activating the workflow...")
    # Activate it via n8n CLI update
    _, o2, e2 = ssh.exec_command(f"docker exec n8n-n8n-1 n8n update:workflow --id={wf_id} --active=true")
    print("ACTIVATE:", o2.read().decode(), e2.read().decode())

ssh.close()
