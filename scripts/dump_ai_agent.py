import json
from shared_config import get_ssh_client

ssh = get_ssh_client()

# Export AI Agent Base workflow full JSON
_, o, _ = ssh.exec_command("docker exec n8n-n8n-1 n8n export:workflow --all")
raw = o.read().decode()
workflows = json.loads(raw)

for wf in workflows:
    if 'AI Agent Base' in wf['name']:
        print(json.dumps(wf, indent=2))
        break

ssh.close()
