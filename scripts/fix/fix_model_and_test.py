import json
import time

from shared_config import (
    N8N_AI_WORKFLOW_ID,
    N8N_CRED_OPENROUTER,
    OPENROUTER_API_KEY,
    get_ssh_client,
)


def main():
    ssh = get_ssh_client()

    # First verify the correct model works
    cmd = (
        f'curl -s https://openrouter.ai/api/v1/chat/completions'
        f' -H "Authorization: Bearer {OPENROUTER_API_KEY}"'
        f' -H "Content-Type: application/json"'
        ' -d \'{"model": "z-ai/glm-4.5-air:free",'
        ' "messages": [{"role": "user", "content": "Di solamente OK"}],'
        " \"max_tokens\": 50}' --max-time 30"
    )
    _, o, _ = ssh.exec_command(cmd)
    time.sleep(20)
    result = o.read().decode()
    print("=== TEST WITH z-ai/glm-4.5-air:free ===")
    print(result[:500])

    # Now fix the workflow with the correct model
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
                            "Eres AgenticOS, un asistente de IA"
                            " conciso. Responde en español."
                            " Sé breve, máximo 2 párrafos."
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
                    "model": {
                        "__rl": True,
                        "value": "=z-ai/glm-4.5-air:free",
                        "mode": "id"
                    },
                    "options": {
                        "maxTokens": 500,
                        "temperature": 0.7
                    }
                },
                "type": "@n8n/n8n-nodes-langchain.lmChatOpenAi",
                "typeVersion": 1.3,
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

    with ssh.open_sftp() as sftp:
        with sftp.file('/tmp/fixed_ai_agent_v2.json', 'w') as f:
            f.write(workflow_json)

    time.sleep(1)
    ssh.exec_command("docker cp /tmp/fixed_ai_agent_v2.json n8n-n8n-1:/tmp/fixed_ai_agent_v2.json")
    time.sleep(1)

    _, o2, e2 = ssh.exec_command("docker exec n8n-n8n-1 n8n import:workflow --input=/tmp/fixed_ai_agent_v2.json")
    time.sleep(3)
    print("\n=== IMPORT ===")
    print(o2.read().decode())

    # Restart n8n to apply changes
    print("Restarting n8n...")
    ssh.exec_command("cd /root/n8n && docker compose restart")
    time.sleep(20)

    # Activate workflow
    _, o3, _ = ssh.exec_command(f"docker exec n8n-n8n-1 n8n update:workflow --id={N8N_AI_WORKFLOW_ID} --active=true")
    time.sleep(3)
    print("ACTIVATE:", o3.read().decode())

    # Test webhook
    print("\n=== TESTING WEBHOOK ===")
    cmd2 = '''curl -s -X POST http://127.0.0.1:5678/webhook/ai-agent \
  -H "Content-Type: application/json" \
  -d '{"chatInput": "Di solamente OK"}' --max-time 45'''
    _, o4, _ = ssh.exec_command(cmd2)
    time.sleep(30)
    print("RESPONSE:", o4.read().decode())

    ssh.close()


if __name__ == "__main__":
    main()
