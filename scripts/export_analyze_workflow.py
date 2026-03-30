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

    # Step 1: Login to n8n API and get cookie
    print("=== LOGGING IN ===")
    login_cmd = (
        'curl -s -c /tmp/n8n_cookies.txt -X POST http://127.0.0.1:5678/rest/login '
        '-H "Content-Type: application/json" '
        f'-d \'{{"emailOrLdapLoginId":"{N8N_EMAIL}","password":"{N8N_PASSWORD}"}}\' '
    )
    _, o, _ = ssh.exec_command(login_cmd)
    time.sleep(3)
    login_resp = o.read().decode()
    print("Login:", "OK" if "id" in login_resp else "FAIL")

    # Step 2: Export the workflow
    print("\n=== EXPORTING WORKFLOW ===")
    export_cmd = f'curl -s -b /tmp/n8n_cookies.txt http://127.0.0.1:5678/rest/workflows/{N8N_AI_WORKFLOW_ID}'
    _, o, _ = ssh.exec_command(export_cmd)
    time.sleep(3)
    wf_json = o.read().decode()
    wf = json.loads(wf_json)
    wf_data = wf.get('data', wf)

    # Step 3: Analyze nodes
    print("\nNodes in workflow:")
    for n in wf_data.get('nodes', []):
        print(f"  - {n['name']} (type: {n['type']}, typeVersion: {n.get('typeVersion')})")

    print("\nConnections:")
    conns = wf_data.get('connections', {})
    print(json.dumps(conns, indent=2)[:1000])

    ssh.close()


if __name__ == "__main__":
    main()
