import json

from shared_config import get_ssh_client


def main():
    ssh = get_ssh_client()

    # Get all workflows
    _, o, _ = ssh.exec_command("docker exec n8n-n8n-1 n8n export:workflow --all")
    raw = o.read().decode()

    workflows = json.loads(raw)
    for wf in workflows:
        if wf['name'] == 'AI Agent Base':
            # Save full workflow to file for analysis
            with open(r'C:\Users\ibrab\Desktop\set up\scripts\ai_agent_base_export.json', 'w') as f:
                json.dump(wf, f, indent=2)
            print(f"AI Agent Base ID: {wf['id']}")
            print(f"Active: {wf.get('active')}")
            print(f"Nodes ({len(wf.get('nodes', []))}):")
            for node in wf.get('nodes', []):
                print(f"  - {node['name']} ({node['type']})")
                if 'credentials' in node:
                    print(f"    Credentials: {json.dumps(node['credentials'])}")
            break

    # Also get credentials list
    _, o2, _ = ssh.exec_command("docker exec n8n-n8n-1 n8n export:credentials --all")
    creds_raw = o2.read().decode()
    try:
        creds = json.loads(creds_raw)
        print("\n=== CREDENTIALS ===")
        for c in creds:
            print(f"  ID: {c['id']} | Name: {c['name']} | Type: {c['type']}")
    except Exception:
        print("Could not parse credentials")

    ssh.close()


if __name__ == "__main__":
    main()
