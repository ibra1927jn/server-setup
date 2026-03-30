import time
import json
from shared_config import (
    get_ssh_client, N8N_EMAIL, N8N_PASSWORD, N8N_AI_WORKFLOW_ID,
)

ssh = get_ssh_client()

w_id = N8N_AI_WORKFLOW_ID

print("1. Logging in...")
ssh.exec_command(f'''curl -s -c /tmp/n8n_cookies.txt -X POST http://127.0.0.1:5678/rest/login \
  -H "Content-Type: application/json" \
  -d '{{"emailOrLdapLoginId":"{N8N_EMAIL}","password":"{N8N_PASSWORD}"}}' ''')
time.sleep(3)

print("2. Downloading workflow...")
_, o, _ = ssh.exec_command(f'''curl -s -b /tmp/n8n_cookies.txt http://127.0.0.1:5678/rest/workflows/{w_id}''')
time.sleep(3)
wf_json = o.read().decode()
wf = json.loads(wf_json)
wf_data = wf.get('data', wf)

print("3. Modifying workflow...")
# Filter out the old model node
new_nodes = [n for n in wf_data['nodes'] if n['name'] != 'OpenAI Chat Model']

# Create a clean OpenRouter model node
chat_model_node = {
    "parameters": {
        "model": "z-ai/glm-4.5-air:free",
        "options": {
            "temperature": 0.7,
            "maxTokens": 500
        }
    },
    "id": "e4f8d5bc-3306-4649-8b4e-250327fcdbc1",
    "name": "OpenAI Chat Model",
    "type": "@n8n/n8n-nodes-langchain.lmChatOpenAi",
    "typeVersion": 1,
    "position": [
        280,
        500
    ],
    "credentials": {
        "openAiApi": {
            "id": "D98S1Z0HkO9oWJ54",  # This is the OpenRouter credential ID from earlier
            "name": "OpenRouter Account"
        }
    }
}
new_nodes.append(chat_model_node)

# Fix connections
conns = wf_data['connections']
# Remove any existing connection TO the chat model
if 'OpenAI Chat Model' in conns:
    del conns['OpenAI Chat Model']

# Ensure the agent has the correct input from the chat model
if 'OpenAI Chat Model' not in conns:
    conns['OpenAI Chat Model'] = {
        "ai_languageModel": [
            [
                {
                    "node": "AI Agent1",
                    "type": "ai_languageModel",
                    "index": 0
                }
            ]
        ]
    }

wf_data['nodes'] = new_nodes
wf_data['connections'] = conns
wf_data['active'] = True

# Write to temp file on remote
remote_patch = '/tmp/wf_patch.json'
sftp = ssh.open_sftp()
with sftp.file(remote_patch, 'w') as f:
    f.write(json.dumps(wf_data, indent=2))
sftp.close()

print("4. Uploading patched workflow...")
upload_cmd = f'''curl -s -b /tmp/n8n_cookies.txt -X PUT http://127.0.0.1:5678/rest/workflows/{w_id} \\
  -H "Content-Type: application/json" \\
  -d @{remote_patch}'''
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
