import time
import json
from shared_config import get_ssh_client, N8N_EMAIL, N8N_PASSWORD

ssh = get_ssh_client()

print("1. Logging in...")
ssh.exec_command(f'''curl -s -c /tmp/n8n_cookies.txt -X POST http://127.0.0.1:5678/rest/login \
  -H "Content-Type: application/json" \
  -d '{{"emailOrLdapLoginId":"{N8N_EMAIL}","password":"{N8N_PASSWORD}"}}' ''')
time.sleep(3)

print("\n2. Getting credentials...")
_, o, _ = ssh.exec_command('''curl -s -b /tmp/n8n_cookies.txt http://127.0.0.1:5678/rest/credentials''')
time.sleep(3)
creds_json = o.read().decode()
try:
    creds = json.loads(creds_json)
    cred_list = creds.get('data', creds)
    for c in cred_list:
        if c.get('type') == 'telegramApi':
            print(f"FOUND TELEGRAM CREDENTIAL: {c.get('name')} | ID: {c.get('id')}")
            valid_id = c.get('id')
except Exception as e:
    print("Error parsing credentials:", e)

print("\n3. Downloading Telegram workflow...")
w_id = '07a5ed10579849f6'
_, o2, _ = ssh.exec_command(f'''curl -s -b /tmp/n8n_cookies.txt http://127.0.0.1:5678/rest/workflows/{w_id}''')
time.sleep(3)
wf_json = o2.read().decode()

try:
    wf = json.loads(wf_json)
    wf_data = wf.get('data', wf)
    
    dirty = False
    for n in wf_data.get('nodes', []):
        if 'credentials' in n and 'telegramApi' in n['credentials']:
            n['credentials']['telegramApi']['id'] = valid_id
            dirty = True
            
    if dirty:
        print(f"4. Updating workflow with valid ID: {valid_id}")
        remote_patch = '/tmp/tg_patch.json'
        sftp = ssh.open_sftp()
        with sftp.file(remote_patch, 'w') as f:
            f.write(json.dumps(wf_data, indent=2))
        sftp.close()
        
        # We need an empty active check first in PUT or just keep whatever it was
        upload_cmd = f'''curl -s -b /tmp/n8n_cookies.txt -X PUT http://127.0.0.1:5678/rest/workflows/{w_id} \
          -H "Content-Type: application/json" \
          -d @{remote_patch}'''
        _, o3, _ = ssh.exec_command(upload_cmd)
        time.sleep(3)
        res = o3.read().decode()
        if "id" in res:
             print("Successfully patched Telegram workflow.")
             # Now activate it
             ssh.exec_command(f'''docker exec n8n-n8n-1 sqlite3 /home/node/.n8n/database.sqlite "UPDATE workflow_entity SET active = 1 WHERE id = '{w_id}';" ''')
             ssh.exec_command('docker restart n8n-n8n-1')
             print("Restarted n8n to apply changes.")
        else:
             print("Failed to save workflow:", res)
             
except Exception as e:
    print("Error updating workflow:", e)

ssh.close()
