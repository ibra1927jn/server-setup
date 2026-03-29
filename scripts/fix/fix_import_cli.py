"""Fix missing workflows by injecting IDs and importing via CLI"""
import json
import os
import random
import string
from shared_config import get_ssh_client

FLOWS_DIR = r"C:\AgenticOS\n8n-flows"
MISSING_FILES = ["server-sentinel.json", "ai-agent-base.json"]

ssh = get_ssh_client()
sftp = ssh.open_sftp()

for f in MISSING_FILES:
    local_path = os.path.join(FLOWS_DIR, f)
    with open(local_path, 'r', encoding='utf-8') as fh:
        data = json.load(fh)
    
    # Inject a random 16-char alphanumeric ID
    random_id = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    data['id'] = random_id
    
    fixed_path = local_path.replace('.json', '-fixed.json')
    with open(fixed_path, 'w', encoding='utf-8') as fh:
        json.dump(data, fh)
    
    remote_path = f"/tmp/n8n-import/{f}"
    print(f"Uploading {f} with new ID {random_id}...")
    sftp.put(fixed_path, remote_path)
    
    print("Copying into container...")
    copy_cmd = f"docker cp {remote_path} n8n-n8n-1:/tmp/n8n-import/{f}"
    ssh.exec_command(copy_cmd)
    
    print("Importing via CLI...")
    import_cmd = f"docker exec n8n-n8n-1 n8n import:workflow --input=/tmp/n8n-import/{f}"
    _, o, e = ssh.exec_command(import_cmd)
    
    print("Out:", o.read().decode().strip())
    print("Err:", e.read().decode().strip())

print("\n=== Verifying ===")
_, o, _ = ssh.exec_command("docker exec n8n-n8n-1 n8n list:workflow")
print(o.read().decode())
sftp.close()
ssh.close()
