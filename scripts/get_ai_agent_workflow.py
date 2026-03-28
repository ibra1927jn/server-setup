import json
from shared_config import get_ssh_client

ssh = get_ssh_client()

# Get all workflows to find the AI Agent Base
_, o, _ = ssh.exec_command("docker exec n8n-n8n-1 n8n export:workflow --all")
raw = o.read().decode()

try:
    workflows = json.loads(raw)
    for wf in workflows:
        print(f"ID: {wf['id']} | Name: {wf['name']} | Active: {wf.get('active', 'N/A')}")
        if wf['name'] == 'AI Agent Base':
            print("\n=== AI AGENT BASE NODES ===")
            for node in wf.get('nodes', []):
                print(f"  - {node['type']} ({node['name']})")
            print("\n=== FULL WORKFLOW JSON ===")
            print(json.dumps(wf, indent=2)[:3000])
except Exception as e:
    print(f"Error: {e}")
    print(raw[:500])

ssh.close()
