"""
Upgrade AI Agent node - Fixed version handling list/dict JSON format.
"""
import json
import time
from shared_config import get_ssh_client, N8N_AI_WORKFLOW_ID


def parse_workflow(raw):
    """Parse workflow JSON that could be a dict or list."""
    data = json.loads(raw)
    if isinstance(data, list):
        return data[0]
    return data


def patch_agent_nodes(wf, target_version=2.1):
    """Patch agent nodes to target version. Returns True if any patched."""
    patched = False
    for node in wf.get('nodes', []):
        if 'agent' in node.get('type', '').lower():
            node['typeVersion'] = target_version
            patched = True
    return patched


def main():
    ssh = get_ssh_client()

    # Export the specific workflow by ID
    print("=== Exporting AI Agent Base workflow ===")
    export_cmd = f"docker exec n8n-n8n-1 n8n export:workflow --id={N8N_AI_WORKFLOW_ID}"
    _, o, e = ssh.exec_command(export_cmd)
    raw = o.read().decode().strip()
    err = e.read().decode().strip()
    if err:
        print("STDERR:", err)

    wf = parse_workflow(raw)

    print(f"Workflow: {wf.get('name')}")
    print(f"Nodes ({len(wf.get('nodes', []))}):")

    for node in wf.get('nodes', []):
        name = node.get('name', '?')
        ntype = node.get('type', '?')
        ver = node.get('typeVersion', '?')
        print(f"  {name} | {ntype} | v{ver}")

    if not patch_agent_nodes(wf):
        print("ERROR: No agent node found!")
        ssh.close()
        exit(1)

    # Save patched workflow to server
    patched_json = json.dumps(wf)
    local_path = r"C:\Users\ibrab\Desktop\set up\scripts\patched_agent.json"
    with open(local_path, 'w', encoding='utf-8') as f:
        f.write(patched_json)

    sftp = ssh.open_sftp()
    sftp.put(local_path, "/tmp/patched_agent.json")
    print("Uploaded patched workflow")

    # Copy into container
    _, o, e = ssh.exec_command("docker cp /tmp/patched_agent.json n8n-n8n-1:/tmp/patched_agent.json")
    o.read()
    e.read()

    # Import
    print("\n=== Importing patched workflow ===")
    _, o, e = ssh.exec_command("docker exec n8n-n8n-1 n8n import:workflow --input=/tmp/patched_agent.json")
    print("OUT:", o.read().decode().strip())
    print("ERR:", e.read().decode().strip())

    # Restart n8n
    print("\n=== Restarting n8n ===")
    _, o, e = ssh.exec_command("docker restart n8n-n8n-1")
    o.read()
    time.sleep(12)
    print("Restarted!")

    # Verify
    print("\n=== Listing workflows ===")
    _, o, _ = ssh.exec_command("docker exec n8n-n8n-1 n8n list:workflow")
    print(o.read().decode().strip())

    sftp.close()
    ssh.close()
    print("\n=== Done! ===")


if __name__ == "__main__":
    main()
