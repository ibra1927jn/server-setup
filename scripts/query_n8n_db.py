import time
from shared_config import get_ssh_client

ssh = get_ssh_client()

# Check the n8n SQLite database for execution errors
# The database is inside the Docker volume
cmd = '''docker exec n8n-n8n-1 sqlite3 /home/node/.n8n/database.sqlite \
  "SELECT id, workflowId, status, stoppedAt FROM execution_entity ORDER BY id DESC LIMIT 5;"'''
_, o, e = ssh.exec_command(cmd)
time.sleep(2)
print("=== RECENT EXECUTIONS ===")
print(o.read().decode())
print(e.read().decode())

# Get execution data with error details
cmd2 = (
    'docker exec n8n-n8n-1 sqlite3'
    ' /home/node/.n8n/database.sqlite'
    ' "SELECT substr(data, 1, 2000)'
    ' FROM execution_data'
    ' WHERE executionId ='
    ' (SELECT id FROM execution_entity'
    ' ORDER BY id DESC LIMIT 1);"'
)
_, o2, e2 = ssh.exec_command(cmd2)
time.sleep(2)
print("\n=== LAST EXECUTION DATA ===")
output = o2.read().decode()
print(output[:2000])

ssh.close()
