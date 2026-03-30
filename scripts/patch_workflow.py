import time
import json
from shared_config import (
    get_ssh_client, N8N_EMAIL, N8N_PASSWORD, N8N_AI_WORKFLOW_ID,
    N8N_CRED_OPENAI,
)


def filter_and_replace_model_node(nodes, old_name, new_node):
    """Remove node by name and append a replacement. Returns new list."""
    filtered = [n for n in nodes if n['name'] != old_name]
    filtered.append(new_node)
    return filtered


def fix_model_connections(conns, model_name, agent_name):
    """Reset connections for a model node pointing to agent. Mutates conns."""
    conns.pop(model_name, None)
    conns[model_name] = {
        "ai_languageModel": [
            [
                {
                    "node": agent_name,
                    "type": "ai_languageModel",
                    "index": 0,
                }
            ]
        ]
    }
    return conns


def build_chat_model_node(
    model="z-ai/glm-4.5-air:free",
    node_id="e4f8d5bc-3306-4649-8b4e-250327fcdbc1",
    cred_id=N8N_CRED_OPENAI,
):
    """Build an OpenRouter chat model node dict."""
    return {
        "parameters": {
            "model": model,
            "options": {
                "temperature": 0.7,
                "maxTokens": 500,
            },
        },
        "id": node_id,
        "name": "OpenAI Chat Model",
        "type": "@n8n/n8n-nodes-langchain.lmChatOpenAi",
        "typeVersion": 1,
        "position": [280, 500],
        "credentials": {
            "openAiApi": {
                "id": cred_id,
                "name": "OpenRouter Account",
            }
        },
    }


def main():
    ssh = get_ssh_client()

    w_id = N8N_AI_WORKFLOW_ID

    print("1. Logging in...")
    ssh.exec_command(
        f'curl -s -c /tmp/n8n_cookies.txt -X POST '
        f'http://127.0.0.1:5678/rest/login '
        f'-H "Content-Type: application/json" '
        f'-d \'{{"emailOrLdapLoginId":"{N8N_EMAIL}",'
        f'"password":"{N8N_PASSWORD}"}}\' '
    )
    time.sleep(3)

    print("2. Downloading workflow...")
    _, o, _ = ssh.exec_command(
        f'curl -s -b /tmp/n8n_cookies.txt '
        f'http://127.0.0.1:5678/rest/workflows/{w_id}'
    )
    time.sleep(3)
    wf_json = o.read().decode()
    wf = json.loads(wf_json)
    wf_data = wf.get('data', wf)

    print("3. Modifying workflow...")
    chat_model_node = build_chat_model_node()
    wf_data['nodes'] = filter_and_replace_model_node(
        wf_data['nodes'], 'OpenAI Chat Model', chat_model_node
    )
    wf_data['connections'] = fix_model_connections(
        wf_data['connections'], 'OpenAI Chat Model', 'AI Agent1'
    )
    wf_data['active'] = True

    remote_patch = '/tmp/wf_patch.json'
    sftp = ssh.open_sftp()
    with sftp.file(remote_patch, 'w') as f:
        f.write(json.dumps(wf_data, indent=2))
    sftp.close()

    print("4. Uploading patched workflow...")
    upload_cmd = (
        f'curl -s -b /tmp/n8n_cookies.txt -X PUT '
        f'http://127.0.0.1:5678/rest/workflows/{w_id} '
        f'-H "Content-Type: application/json" '
        f'-d @{remote_patch}'
    )
    _, o2, stderr = ssh.exec_command(upload_cmd)
    time.sleep(3)
    result = o2.read().decode()
    err = stderr.read().decode()

    print("RAW RESPONSE:")
    print(result)
    print("STDERR:", err)

    try:
        res_json = json.loads(result)
        parsed_id = res_json.get('data', res_json).get('id')
        print(f"Patched Workflow ID: {parsed_id}")
    except Exception as e:
        print("Failed to decode JSON:", e)

    ssh.close()


if __name__ == "__main__":
    main()
