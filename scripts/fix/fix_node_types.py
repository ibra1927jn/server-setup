"""
Fix Daily Briefing and Uptime Monitor: replace executeCommand with SSH node.
The n8n Docker image doesn't have executeCommand node available.
The working Server Sentinel uses n8n-nodes-base.ssh for remote commands.
"""

import json
import time

from shared_config import N8N_CRED_SSH, get_ssh_client


def print_sentinel_nodes(all_wfs):
    """Print SSH node details from the Server Sentinel workflow."""
    for wf in all_wfs:
        if "Sentinel" in wf.get("name", ""):
            print(f"=== {wf['name']} ===")
            for node in wf.get("nodes", []):
                t = node.get("type", "")
                print(f"  {node['name']} -> {t} v{node.get('typeVersion')}")
                if "ssh" in t.lower():
                    print(f"    PARAMS: {json.dumps(node.get('parameters', {}), indent=2)[:300]}")
                    print(f"    CREDS: {json.dumps(node.get('credentials', {}))}")


def replace_execute_command_nodes(wf):
    """Replace executeCommand nodes with SSH nodes. Returns True if any changed."""
    changed = False
    for node in wf.get("nodes", []):
        if node.get("type") == "n8n-nodes-base.executeCommand":
            old_cmd = node["parameters"].get("command", "")
            print("  Replacing executeCommand -> ssh")
            print(f"  Command: {old_cmd[:100]}...")
            node["type"] = "n8n-nodes-base.ssh"
            node["typeVersion"] = 1
            node["parameters"] = {"command": old_cmd, "authentication": "password"}
            node["credentials"] = {"sshPassword": {"id": N8N_CRED_SSH, "name": "Hetzner Root SSH"}}
            changed = True
    return changed


def upload_and_import(ssh, sftp, wf, name):
    """Upload fixed workflow JSON and import it into n8n."""
    slug = name.replace(" ", "_").lower()
    local_path = f"/tmp/fixed_{slug}.json"
    with open(local_path, "w", encoding="utf-8") as f:
        json.dump(wf, f)

    remote_path = f"/tmp/n8n-import/fixed_{slug}.json"
    sftp.put(local_path, remote_path)
    ssh.exec_command(f"docker cp {remote_path} n8n-n8n-1:{remote_path}")
    time.sleep(1)

    _, o, e = ssh.exec_command(f"docker exec n8n-n8n-1 n8n import:workflow --input={remote_path}")
    print(f"  Import: {o.read().decode().strip()}")
    err = e.read().decode().strip()
    if err:
        print(f"  Err: {err}")


def main():
    ssh = get_ssh_client()

    _, o, _ = ssh.exec_command("docker exec n8n-n8n-1 n8n export:workflow --all")
    all_wfs = json.loads(o.read().decode().strip())

    print_sentinel_nodes(all_wfs)

    sftp = ssh.open_sftp()
    for wf in all_wfs:
        name = wf.get("name", "")
        if name not in ["Daily Briefing", "Uptime Monitor"]:
            continue
        print(f"\n=== FIXING: {name} ===")
        if replace_execute_command_nodes(wf):
            upload_and_import(ssh, sftp, wf, name)

    print("\n=== Restarting n8n ===")
    ssh.exec_command("docker restart n8n-n8n-1")
    time.sleep(12)

    _, o, _ = ssh.exec_command("docker exec n8n-n8n-1 n8n list:workflow")
    print("\n=== FINAL WORKFLOWS ===")
    print(o.read().decode().strip())

    sftp.close()
    ssh.close()
    print("\nDone!")


if __name__ == "__main__":
    main()
