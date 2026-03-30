import json

from shared_config import get_ssh_client


def main():
    ssh = get_ssh_client()

    # Get the AI Agent Base workflow details
    _, o, _ = ssh.exec_command("docker exec n8n-n8n-1 n8n export:workflow --all")
    raw = o.read().decode()
    workflows = json.loads(raw)

    for wf in workflows:
        if "Agent" in wf["name"] or "agent" in wf["name"] or "AI" in wf["name"]:
            print(f"\n=== {wf['name']} (ID: {wf['id']}, Active: {wf.get('active')}) ===")
            for node in wf.get("nodes", []):
                print(f"  Node: {node['name']} ({node['type']})")
                if "webhook" in node["type"].lower() or "trigger" in node["type"].lower():
                    print(f"    Params: {json.dumps(node.get('parameters', {}), indent=4)}")

    # Also list all active webhooks
    print("\n=== ALL WEBHOOK NODES ===")
    for wf in workflows:
        for node in wf.get("nodes", []):
            if "webhook" in node["type"].lower():
                path = node.get("parameters", {}).get("path", "N/A")
                print(f"  WF: {wf['name']} | Node: {node['name']} | Path: {path}")

    ssh.close()


if __name__ == "__main__":
    main()
