"""Ejecutar cada workflow nuevo individualmente y capturar errores"""
import json
import time
from shared_config import get_ssh_client


def main():
    ssh = get_ssh_client()

    _, o, _ = ssh.exec_command("docker exec n8n-n8n-1 n8n export:workflow --all")
    wfs = json.loads(o.read().decode().strip())

    targets = ["Crypto Portfolio Alerts", "Daily Briefing", "Uptime Monitor", "GitHub Auto-Backup"]

    for wf in wfs:
        name = wf.get("name", "")
        if name not in targets:
            continue

        wid = wf["id"]
        print(f"\n{'='*50}")
        print(f"WORKFLOW: {name} ({wid})")
        print(f"{'='*50}")
        print(f"Active: {wf.get('active')}")

        # Show nodes detail
        for n in wf.get("nodes", []):
            creds = n.get("credentials", {})
            print(f"  Node: {n['name']} | Type: {n['type']} | Creds: {json.dumps(creds)}")

        # Execute and capture FULL output
        print("\n  Executing...")
        _, o, e = ssh.exec_command(f"docker exec n8n-n8n-1 n8n execute --id={wid} 2>&1", timeout=30)
        try:
            full_out = o.read().decode().strip()
            full_err = e.read().decode().strip()
            print(f"  STDOUT: {full_out[:300]}")
            if full_err:
                print(f"  STDERR: {full_err[:300]}")
        except Exception as ex:
            print(f"  Exception: {ex}")

        time.sleep(2)

    ssh.close()
    print("\nDone!")


if __name__ == "__main__":
    main()
