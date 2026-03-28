"""
Upgrade AI Agent node - Fixed version handling list/dict JSON format.
"""
import json
import time
from shared_config import get_ssh_client

ssh = get_ssh_client()

# Export the specific workflow by ID
print("=== Exporting AI Agent Base workflow ===")
export_cmd = "docker exec n8n-n8n-1 n8n export:workflow --id=WiTcSI66bHwdSgkd"
_, o, e = ssh.exec_command(export_cmd)
raw = o.read().decode().strip()
err = e.read().decode().strip()
if err:
    print("STDERR:", err)

# Parse - could be dict or list
data = json.loads(raw)
if isinstance(data, list):
    wf = data[0]
    print(f"Parsed as list, using first element")
else:
    wf = data
    print(f"Parsed as dict")

print(f"Workflow: {wf.get('name')}")
print(f"Nodes ({len(wf.get('nodes', []))}):")

for node in wf.get('nodes', []):
    name = node.get('name', '?')
    ntype = node.get('type', '?')
    ver = node.get('typeVersion', '?')
    print(f"  {name} | {ntype} | v{ver}")

# Patch the AI Agent node version
patched = False
for node in wf.get('nodes', []):
    if 'agent' in node.get('type', '').lower():
        old_ver = node.get('typeVersion')
        node['typeVersion'] = 2.1
        print(f"\n>>> PATCHED: {node['name']} v{old_ver} -> v2.1")
        patched = True

if not patched:
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
o.read(); e.read()

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
