import json
import time

from shared_config import (
    N8N_AI_WORKFLOW_ID,
    N8N_CRED_OPENROUTER,
    get_ssh_client,
)


def main():
    ssh = get_ssh_client()

    # Replace the AI Agent Base workflow with a simpler version that uses typeVersion 1.7
    # This avoids the Python task runner requirement
    fixed_workflow = {
        "id": N8N_AI_WORKFLOW_ID,
        "name": "AI Agent Base - Template con Memoria",
        "active": True,
        "nodes": [
            {
                "parameters": {
                    "httpMethod": "POST",
                    "path": "ai-agent",
                    "responseMode": "lastNode",
                    "options": {}
                },
                "id": "webhook-input",
                "name": "Webhook Input",
                "type": "n8n-nodes-base.webhook",
                "typeVersion": 2,
                "position": [224, 304],
                "webhookId": "ai-agent-endpoint"
            },
            {
                "parameters": {
                    "promptType": "define",
                    "text": "={{ $json.body.chatInput }}",
                    "options": {
                        "systemMessage": (
                            "Eres AgenticOS, un asistente de IA conciso."
                            " Responde en español. Sé breve, máximo"
                            " 2 párrafos. Si no sabes algo,"
                            " dilo honestamente."
                        )
                    }
                },
                "type": "@n8n/n8n-nodes-langchain.agent",
                "typeVersion": 1.7,
                "position": [448, 304],
                "id": "ai-agent-node",
                "name": "AI Agent1"
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
                "position": [456, 528],
                "id": "openrouter-model-node",
                "name": "OpenAI Chat Model",
                "credentials": {
                    "openAiApi": {
                        "id": N8N_CRED_OPENROUTER,
                        "name": "OpenRouter Account"
                    }
                }
            },
            {
                "parameters": {
                    "sessionIdType": "customKey",
                    "sessionKey": "={{ $json.body.session_id || 'default' }}",
                    "contextWindowLength": 10
                },
                "id": "memory",
                "name": "Window Buffer Memory",
                "type": "@n8n/n8n-nodes-langchain.memoryBufferWindow",
                "typeVersion": 1.3,
                "position": [584, 528]
            }
        ],
        "connections": {
            "Webhook Input": {
                "main": [
                    [{"node": "AI Agent1", "type": "main", "index": 0}]
                ]
            },
            "OpenAI Chat Model": {
                "ai_languageModel": [
                    [{"node": "AI Agent1", "type": "ai_languageModel", "index": 0}]
                ]
            },
            "Window Buffer Memory": {
                "ai_memory": [
                    [{"node": "AI Agent1", "type": "ai_memory", "index": 0}]
                ]
            }
        },
        "settings": {
            "executionOrder": "v1"
        }
    }

    workflow_json = json.dumps([fixed_workflow])

    with ssh.open_sftp() as sftp, sftp.file('/tmp/fixed_ai_agent.json', 'w') as f:
        f.write(workflow_json)

    time.sleep(1)
    ssh.exec_command(
        "docker cp /tmp/fixed_ai_agent.json"
        " n8n-n8n-1:/tmp/fixed_ai_agent.json"
    )
    time.sleep(1)

    cmd = (
        "docker exec n8n-n8n-1 n8n import:workflow"
        " --input=/tmp/fixed_ai_agent.json"
    )
    _, o, e = ssh.exec_command(cmd)
    print("IMPORT:", o.read().decode())
    print("STDERR:", e.read().decode())

    time.sleep(2)

    # Activate the workflow
    cmd = (
        "docker exec n8n-n8n-1 n8n update:workflow"
        f" --id={N8N_AI_WORKFLOW_ID} --active=true"
    )
    _, o2, e2 = ssh.exec_command(cmd)
    time.sleep(3)
    print("ACTIVATE:", o2.read().decode())

    # Now test the webhook
    print("\n=== TESTING FIXED WEBHOOK ===")
    cmd = '''curl -s -X POST http://127.0.0.1:5678/webhook/ai-agent \
  -H "Content-Type: application/json" \
  -d '{"chatInput": "Di OK"}' --max-time 30'''
    _, o3, _ = ssh.exec_command(cmd)
    time.sleep(20)
    print("RESPONSE:", o3.read().decode())

    ssh.close()


if __name__ == "__main__":
    main()
