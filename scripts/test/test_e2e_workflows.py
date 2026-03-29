"""
MEJORA 1: Test E2E de todos los workflows nuevos
Ejecuta manualmente cada workflow y verifica que Telegram recibe los mensajes.
"""
import json, time
from shared_config import get_ssh_client


def main():
    ssh = get_ssh_client()

    # First, get all workflow IDs
    _, o, _ = ssh.exec_command("docker exec n8n-n8n-1 n8n export:workflow --all")
    raw = o.read().decode().strip()
    all_wfs = json.loads(raw)

    wf_map = {}
    for wf in all_wfs:
        wf_map[wf["name"]] = wf["id"]
        print(f"  {wf['name']} -> {wf['id']} (active: {wf.get('active')})")

    # Test each new workflow by executing via n8n internal CLI
    workflows_to_test = ["Daily Briefing", "Uptime Monitor", "Crypto Portfolio Alerts", "GitHub Auto-Backup"]

    print("\n" + "=" * 50)
    print("TESTING E2E - WORKFLOWS NUEVOS")
    print("=" * 50)

    for wf_name in workflows_to_test:
        wf_id = wf_map.get(wf_name)
        if not wf_id:
            print(f"\n[SKIP] {wf_name} - Not found!")
            continue

        print(f"\n--- Testing: {wf_name} ({wf_id}) ---")

        # Execute workflow manually via n8n CLI
        cmd = f"docker exec n8n-n8n-1 n8n execute --id={wf_id} 2>&1"
        print(f"  Executing...")
        _, o, e = ssh.exec_command(cmd, timeout=30)

        try:
            out = o.read().decode().strip()
            err = e.read().decode().strip()
        except Exception as ex:
            out = ""
            err = str(ex)

        if "error" in (out + err).lower():
            print(f"  [FAIL] Error: {(out + err)[:200]}")
        else:
            print(f"  [OK] Execution completed")
            if out: print(f"  Output: {out[:150]}")

        time.sleep(2)

    ssh.close()
    print("\n" + "=" * 50)
    print("Test completado. Revisa Telegram para ver si llegaron los mensajes.")
    print("=" * 50)


if __name__ == "__main__":
    main()
