"""Check execution result and logs after workflow rebuild"""

import time

from shared_config import get_ssh_client

ssh = get_ssh_client()

# Check docker logs for EVERYTHING in the last 2 minutes
print("=== DOCKER LOGS (last 100 lines) ===")
_, o, _ = ssh.exec_command("docker logs n8n-n8n-1 --tail 100 2>&1")
logs = o.read().decode().strip()
for line in logs.split("\n"):
    # Print lines with useful info
    ll = line.lower()
    if any(k in ll for k in ["error", "fail", "telegram", "cred", "execut", "warn", "success", "node", "active"]):
        print(f"  {line.strip()[:200]}")

# Execute Crypto Alerts one more time with detailed tracking
print("\n=== EXECUTING CRYPTO ALERTS ===")
_, o, _ = ssh.exec_command("docker exec n8n-n8n-1 n8n list:workflow")
lines = o.read().decode().strip()
print(lines)

for line in lines.split("\n"):
    if "Crypto" in line:
        wid = line.split("|")[0].strip()
        print(f"\nRunning workflow {wid}...")

        # Clear recent logs first
        _, o, _ = ssh.exec_command("docker logs n8n-n8n-1 --tail 1 2>&1")
        o.read()

        # Execute
        _, o, e = ssh.exec_command(f"docker exec n8n-n8n-1 n8n execute --id={wid} 2>&1", timeout=30)
        try:
            out = o.read().decode()
            print(f"Execute output: {out[:500]}")
        except Exception:
            print("(timeout)")

        time.sleep(3)

        # Get NEW logs that appeared during execution
        print("\n=== LOGS DURING EXECUTION ===")
        _, o, _ = ssh.exec_command("docker logs n8n-n8n-1 --tail 20 2>&1")
        new_logs = o.read().decode().strip()
        print(new_logs)
        break

ssh.close()
