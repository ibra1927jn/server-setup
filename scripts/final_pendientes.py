"""
Final 2 pendientes:
1. Publicar TODOS los workflows via n8n REST API
2. Configurar backup automatico de la DB de n8n
"""

import time

from shared_config import get_ssh_client


def parse_workflow_ids(output):
    """Parse workflow IDs from 'n8n list:workflow' output.

    Each line with '|' is treated as 'id | name'.
    Returns list of (id, name) tuples.
    """
    results = []
    for line in output.strip().split("\n"):
        if "|" in line:
            parts = line.split("|")
            wf_id = parts[0].strip()
            wf_name = parts[1].strip()
            results.append((wf_id, wf_name))
    return results


BACKUP_SCRIPT = """#!/bin/bash
# AgenticOS n8n Backup Script
# Runs daily, keeps last 7 backups

BACKUP_DIR="/root/n8n-backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Copy the n8n data volume
docker cp n8n-n8n-1:/home/node/.n8n/database.sqlite \
  $BACKUP_DIR/n8n_db_$TIMESTAMP.sqlite 2>/dev/null

# Also export all workflows as JSON
docker exec n8n-n8n-1 n8n export:workflow --all \
  --output=/tmp/n8n_workflows_backup.json 2>/dev/null
docker cp n8n-n8n-1:/tmp/n8n_workflows_backup.json \
  $BACKUP_DIR/workflows_$TIMESTAMP.json 2>/dev/null

# Export credentials (encrypted)
docker exec n8n-n8n-1 n8n export:credentials --all \
  --output=/tmp/n8n_creds_backup.json 2>/dev/null
docker cp n8n-n8n-1:/tmp/n8n_creds_backup.json \
  $BACKUP_DIR/credentials_$TIMESTAMP.json 2>/dev/null

# Remove backups older than 7 days
find $BACKUP_DIR -name "*.sqlite" -mtime +7 -delete
find $BACKUP_DIR -name "*.json" -mtime +7 -delete

echo "[$(date)] Backup completed: n8n_db_$TIMESTAMP.sqlite"
"""


def publish_workflows(ssh):
    """Publish all n8n workflows via REST API or CLI fallback."""
    print("=" * 50)
    print("PASO 1: PUBLICANDO WORKFLOWS")
    print("=" * 50)

    _, o, _ = ssh.exec_command("docker exec n8n-n8n-1 n8n list:workflow")
    lines = o.read().decode().strip()
    wf_ids = parse_workflow_ids(lines)
    for wf_id, wf_name in wf_ids:
        print(f"  Found: {wf_name} ({wf_id})")

    # Activate each workflow using the internal REST API via curl
    for wf_id, wf_name in wf_ids:
        print(f"\n  Publishing: {wf_name}...")
        cmd = (
            f'docker exec n8n-n8n-1 sh -c "curl -s -X PATCH '
            f"http://localhost:5678/api/v1/workflows/{wf_id} "
            f"-H 'Content-Type: application/json' "
            f"""-d '{{\\\"active\\\": true}}' 2>/dev/null | head -c 200\""""
        )
        _, o, _e = ssh.exec_command(cmd)
        out = o.read().decode().strip()
        if "active" in out:
            print("    OK - activated via API")
        else:
            _, o2, _e2 = ssh.exec_command(f"docker exec n8n-n8n-1 n8n update:workflow --id={wf_id} --active=true")
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


def setup_backup(ssh):
    """Install and run the n8n backup script with daily cron."""
    print("\n" + "=" * 50)
    print("PASO 2: BACKUP AUTOMATICO DB N8N")
    print("=" * 50)

    print("  Creating backup script...")
    write_cmd = f"cat > /root/n8n-backup.sh << 'HEREDOC'\n{BACKUP_SCRIPT}\nHEREDOC\nchmod +x /root/n8n-backup.sh"
    _, o, e = ssh.exec_command(write_cmd)
    o.read()
    e.read()

    print("  Running first backup...")
    _, o, e = ssh.exec_command("bash /root/n8n-backup.sh")
    out = o.read().decode().strip()
    err = e.read().decode().strip()
    if out:
        print(f"    {out}")
    if err:
        print(f"    ERR: {err}")

    # Set up cron job - daily at 3:00 AM
    print("  Setting up daily cron (3:00 AM)...")
    cron_cmd = (
        "(crontab -l 2>/dev/null | grep -v n8n-backup; "
        'echo "0 3 * * * /root/n8n-backup.sh '
        '>> /var/log/n8n-backup.log 2>&1") | crontab -'
    )
    _, o, e = ssh.exec_command(cron_cmd)
    o.read()
    e.read()

    # Verify cron
    _, o, _ = ssh.exec_command("crontab -l")
    print(f"  Cron jobs:\n{o.read().decode().strip()}")

    # Verify backup files
    print("\n  Backup files:")
    _, o, _ = ssh.exec_command("ls -lh /root/n8n-backups/")
    print(o.read().decode().strip())


def main():
    ssh = get_ssh_client()
    publish_workflows(ssh)
    setup_backup(ssh)
    ssh.close()
    print("\n" + "=" * 50)
    print("COMPLETADO!")
    print("=" * 50)


if __name__ == "__main__":
    main()
