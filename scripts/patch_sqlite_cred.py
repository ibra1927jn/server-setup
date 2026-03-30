import time
from shared_config import (
    get_ssh_client, N8N_CRED_TELEGRAM_BOT, N8N_CRED_TELEGRAM,
    N8N_TELEGRAM_BOT_WORKFLOW_ID,
)

ssh = get_ssh_client()

w_id = N8N_TELEGRAM_BOT_WORKFLOW_ID
old_cred = N8N_CRED_TELEGRAM_BOT
new_cred = N8N_CRED_TELEGRAM

print("=== PATCHING SQLITE DIRECTLY ===")
patch_cmd = f'''docker exec n8n-n8n-1 sqlite3 /home/node/.n8n/database.sqlite \
  "UPDATE workflow_entity SET nodes = REPLACE(nodes, '{old_cred}', '{new_cred}'), active = 1 WHERE id = '{w_id}';" '''
ssh.exec_command(patch_cmd)

time.sleep(1)
print("=== RESTARTING N8N ===")
ssh.exec_command('docker restart n8n-n8n-1')
time.sleep(15)  # allow n8n to booth

print("=== CHECKING FOR TELEGRAM ERRORS IN LOGS ===")
_, o2, _ = ssh.exec_command('docker logs n8n-n8n-1 --tail 50')
print("LOGS:", o2.read().decode()[-2000:])

ssh.close()
