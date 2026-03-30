import json
import time

from shared_config import (
    N8N_AI_WORKFLOW_ID,
    N8N_EMAIL,
    N8N_PASSWORD,
    get_ssh_client,
)


def main():
    ssh = get_ssh_client()

    # Login first
    login_cmd = (
        "curl -s -c /tmp/n8n_cookies.txt"
        " -X POST http://127.0.0.1:5678/rest/login"
        ' -H "Content-Type: application/json"'
        f""" -d '{{"emailOrLdapLoginId":"{N8N_EMAIL}","""
        f""""password":"{N8N_PASSWORD}"}}'"""
    )
    ssh.exec_command(login_cmd)
    time.sleep(3)

    # Check execution log
    print("=== LATEST EXECUTIONS ===")
    _, o, _ = ssh.exec_command(
        f'curl -s -b /tmp/n8n_cookies.txt "http://127.0.0.1:5678/rest/executions?workflowId={N8N_AI_WORKFLOW_ID}&limit=5"'
    )
    time.sleep(3)
    resp = o.read().decode()
    try:
        data = json.loads(resp)
        execs = data.get("data", data.get("results", []))
        if isinstance(execs, dict):
            execs = execs.get("results", [])
        for ex in execs[:3]:
            eid = ex.get("id", "unknown")
            status = ex.get("status", "unknown")
            finished = ex.get("stoppedAt", "N/A")
            print(f"\nExecution {eid}: status={status}, finished={finished}")
            # Get full details for the most recent failed one
            if status in ["error", "failed", "crashed"]:
                _, o2, _ = ssh.exec_command(f'curl -s -b /tmp/n8n_cookies.txt "http://127.0.0.1:5678/rest/executions/{eid}"')
                time.sleep(3)
                detail = o2.read().decode()
                try:
                    d = json.loads(detail)
                    exec_data = d.get("data", d)
                    # Get error message from the execution
                    result_data = exec_data.get("data", exec_data).get("resultData", {})
                    error = result_data.get("error", {})
                    if error:
                        print(f"  ERROR: {json.dumps(error, indent=2)[:500]}")
                    run_data = result_data.get("runData", {})
                    for node_name, runs in run_data.items():
                        for r in runs:
                            if r.get("error"):
                                err_str = json.dumps(r["error"], indent=2)[:300]
                                print(f"  Node '{node_name}' error: {err_str}")
                except Exception:
                    print(f"  Raw detail: {detail[:300]}")
                break
    except Exception as e:
        print(f"Parse error: {e}")
        print(f"Raw: {resp[:500]}")

    ssh.close()


if __name__ == "__main__":
    main()
