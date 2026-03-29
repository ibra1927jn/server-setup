import json
import time
from shared_config import get_ssh_client

ssh = get_ssh_client()

# Build the Telegram AI Bot workflow
telegram_ai_workflow = {
    "name": "Telegram AI Bot",
    "nodes": [
        {
            "parameters": {
                "updates": ["message"]
            },
            "type": "n8n-nodes-base.telegramTrigger",
            "typeVersion": 1.1,
            "position": [220, 300],
            "id": "telegram-trigger-node",
            "name": "Telegram Trigger",
            "credentials": {
                "telegramApi": {
                    "id": "GoCsBqVPx05691Ng",
                    "name": "Telegram account"
                }
            }
        },
        {
            "parameters": {
                "options": {
                    "systemMessage": "Eres un asistente de IA conciso y útil llamado AgenticOS. Responde en español. Sé breve y directo, máximo 2 párrafos. Si no sabes algo, dilo honestamente."
                }
            },
            "type": "@n8n/n8n-nodes-langchain.agent",
            "typeVersion": 1.7,
            "position": [480, 300],
            "id": "ai-agent-node",
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
            "id": "openrouter-model-node",
            "name": "GLM-4.5 Air",
            "credentials": {
                "openAiApi": {
                    "id": "KViDucLPeGURRcAd",
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

# Write workflow JSON to server
workflow_json = json.dumps([telegram_ai_workflow])
escaped_json = workflow_json.replace("'", "'\\''")

# Write to a temp file on the server
ssh.exec_command(f"echo '{escaped_json}' > /tmp/telegram_ai_bot.json")

time.sleep(1)

# Verify file was written
_, o, _ = ssh.exec_command("wc -c /tmp/telegram_ai_bot.json")
print("File size:", o.read().decode().strip())

# Import via CLI
_, o, e = ssh.exec_command("docker exec -i n8n-n8n-1 n8n import:workflow --input=/tmp/telegram_ai_bot.json")
print("STDOUT:", o.read().decode())
print("STDERR:", e.read().decode())

ssh.close()
