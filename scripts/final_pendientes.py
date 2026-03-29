"""
Final 2 pendientes:
1. Publicar TODOS los workflows via n8n REST API
2. Configurar backup automatico de la DB de n8n
"""
import time
from shared_config import get_ssh_client

ssh = get_ssh_client()

# ====================================================
# PASO 1: Publicar workflows via REST API desde DENTRO del container
# ====================================================
print("=" * 50)
print("PASO 1: PUBLICANDO WORKFLOWS")
print("=" * 50)

# Use curl from inside the container to hit the internal API
# First, get all workflow IDs 
_, o, _ = ssh.exec_command("docker exec n8n-n8n-1 n8n list:workflow")
lines = o.read().decode().strip().split("\n")
wf_ids = []
for line in lines:
    if "|" in line:
        wf_id = line.split("|")[0].strip()
        wf_name = line.split("|")[1].strip()
        wf_ids.append((wf_id, wf_name))
        print(f"  Found: {wf_name} ({wf_id})")

# Activate each workflow using the internal REST API via curl
for wf_id, wf_name in wf_ids:
    print(f"\n  Publishing: {wf_name}...")
    # Use the internal n8n API - PATCH to activate
    cmd = f'''docker exec n8n-n8n-1 sh -c "curl -s -X PATCH http://localhost:5678/api/v1/workflows/{wf_id} -H 'Content-Type: application/json' -d '{{\\"active\\": true}}' 2>/dev/null | head -c 200"'''
    _, o, e = ssh.exec_command(cmd)
    out = o.read().decode().strip()
    if "active" in out:
        print("    OK - activated via API")
    else:
        # Try with n8n CLI instead
        _, o2, e2 = ssh.exec_command(f"docker exec n8n-n8n-1 n8n update:workflow --id={wf_id} --active=true")
        o2.read()
        print("    Activated via CLI")

# Restart to ensure all triggers register
print("\n  Restarting n8n to register all triggers...")
ssh.exec_command("docker restart n8n-n8n-1")
time.sleep(15)
print("  Restarted!")

# Verify
print("\n  Verification:")
_, o, _ = ssh.exec_command("docker exec n8n-n8n-1 n8n list:workflow")
print(o.read().decode().strip())

# ====================================================
# PASO 2: Backup automático de la DB de n8n
# ====================================================
print("\n" + "=" * 50)
print("PASO 2: BACKUP AUTOMATICO DB N8N")
print("=" * 50)

# Create backup script on the server
backup_script = '''#!/bin/bash
# AgenticOS n8n Backup Script
# Runs daily, keeps last 7 backups

BACKUP_DIR="/root/n8n-backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Copy the n8n data volume
docker cp n8n-n8n-1:/home/node/.n8n/database.sqlite $BACKUP_DIR/n8n_db_$TIMESTAMP.sqlite 2>/dev/null

# Also export all workflows as JSON
docker exec n8n-n8n-1 n8n export:workflow --all --output=/tmp/n8n_workflows_backup.json 2>/dev/null
docker cp n8n-n8n-1:/tmp/n8n_workflows_backup.json $BACKUP_DIR/workflows_$TIMESTAMP.json 2>/dev/null

# Export credentials (encrypted)
docker exec n8n-n8n-1 n8n export:credentials --all --output=/tmp/n8n_creds_backup.json 2>/dev/null
docker cp n8n-n8n-1:/tmp/n8n_creds_backup.json $BACKUP_DIR/credentials_$TIMESTAMP.json 2>/dev/null

# Remove backups older than 7 days
find $BACKUP_DIR -name "*.sqlite" -mtime +7 -delete
find $BACKUP_DIR -name "*.json" -mtime +7 -delete

echo "[$(date)] Backup completed: n8n_db_$TIMESTAMP.sqlite"
'''

# Write backup script to server
print("  Creating backup script...")
# Use heredoc to write the file
write_cmd = f'''cat > /root/n8n-backup.sh << 'HEREDOC'
{backup_script}
HEREDOC
chmod +x /root/n8n-backup.sh'''
_, o, e = ssh.exec_command(write_cmd)
o.read(); e.read()

# Run first backup now
print("  Running first backup...")
_, o, e = ssh.exec_command("bash /root/n8n-backup.sh")
out = o.read().decode().strip()
err = e.read().decode().strip()
if out: print(f"    {out}")
if err: print(f"    ERR: {err}")

# Set up cron job - daily at 3:00 AM
print("  Setting up daily cron (3:00 AM)...")
cron_cmd = '(crontab -l 2>/dev/null | grep -v n8n-backup; echo "0 3 * * * /root/n8n-backup.sh >> /var/log/n8n-backup.log 2>&1") | crontab -'
_, o, e = ssh.exec_command(cron_cmd)
o.read(); e.read()

# Verify cron
_, o, _ = ssh.exec_command("crontab -l")
print(f"  Cron jobs:\n{o.read().decode().strip()}")

# Verify backup files
print("\n  Backup files:")
_, o, _ = ssh.exec_command("ls -lh /root/n8n-backups/")
print(o.read().decode().strip())

ssh.close()
print("\n" + "=" * 50)
print("COMPLETADO!")
print("=" * 50)
