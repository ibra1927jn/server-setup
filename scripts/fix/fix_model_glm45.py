"""
FIX: Corregir el modelo del OpenAI Chat Model a z-ai/glm-4.5-air:free
El browser subagent puso gpt-5-mini por error. El usuario eligio GLM-4.5 Air.
"""

import json
import time

import requests
from shared_config import N8N_AI_WORKFLOW_ID, VPS_HOST, get_ssh_client


def _patch_model_nodes(wf, model="z-ai/glm-4.5-air:free"):
    """Patch OpenAI Chat Model nodes to use the correct model."""
    for node in wf.get("nodes", []):
        if "openai" in node.get("type", "").lower():
            old_model = node["parameters"].get("model", {})
            print(f"\nNodo: {node['name']}")
            print(f"  Modelo ANTERIOR: {json.dumps(old_model)}")
            node["parameters"]["model"] = {"__rl": True, "value": f"={model}", "mode": "raw"}
            print(f"  Modelo NUEVO: {model}")
            print(f"  Credenciales: {json.dumps(node.get('credentials', {}))}")


def _upload_and_import(ssh, wf):
    """Save workflow JSON locally, upload via SFTP, and import into n8n."""
    patched_json = json.dumps(wf)
    local_path = "/tmp/patched_glm45.json"
    with open(local_path, "w", encoding="utf-8") as f:
        f.write(patched_json)

    sftp = ssh.open_sftp()
    sftp.put(local_path, "/tmp/patched_glm45.json")
    ssh.exec_command("docker cp /tmp/patched_glm45.json n8n-n8n-1:/tmp/patched_glm45.json")

    print("\n=== Importando workflow corregido ===")
    cmd = "docker exec n8n-n8n-1 n8n import:workflow --input=/tmp/patched_glm45.json"
    _, o, e = ssh.exec_command(cmd)
    print("OUT:", o.read().decode().strip())
    print("ERR:", e.read().decode().strip())
    return sftp


def main():
    ssh = get_ssh_client()

    # Export workflow
    print("=== Exportando workflow ===")
    cmd = f"docker exec n8n-n8n-1 n8n export:workflow --id={N8N_AI_WORKFLOW_ID}"
    _, o, _ = ssh.exec_command(cmd)
    raw = o.read().decode().strip()
    data = json.loads(raw)
    wf = data[0] if isinstance(data, list) else data

    print(f"Workflow: {wf['name']}")

    _patch_model_nodes(wf)
    sftp = _upload_and_import(ssh, wf)

    # Activate
    print("\n=== Activando workflow ===")
    cmd = f"docker exec n8n-n8n-1 n8n update:workflow --id={N8N_AI_WORKFLOW_ID} --active=true"
    _, o, _e = ssh.exec_command(cmd)
    print("OUT:", o.read().decode().strip())

    # Restart n8n
    print("\n=== Reiniciando n8n ===")
    ssh.exec_command("docker restart n8n-n8n-1")
    time.sleep(15)
    print("n8n reiniciado!")

    # Verify the fix
    print("\n=== VERIFICACION: Modelo actual ===")
    cmd = f"docker exec n8n-n8n-1 n8n export:workflow --id={N8N_AI_WORKFLOW_ID}"
    _, o, _ = ssh.exec_command(cmd)
    raw2 = o.read().decode().strip()
    data2 = json.loads(raw2)
    wf2 = data2[0] if isinstance(data2, list) else data2
    for node in wf2.get("nodes", []):
        if "openai" in node.get("type", "").lower():
            model = node["parameters"].get("model", {})
            print(f"  {node['name']}: modelo = {json.dumps(model)}")

    sftp.close()
    ssh.close()

    # Test webhook
    print("\n=== TESTING WEBHOOK ===")
    try:
        r = requests.post(
            f"http://{VPS_HOST}:5678/webhook/ai-agent",
            json={"chatInput": "Hola! Dime que modelo de IA eres y confirma que estas online."},
            timeout=60,
        )
        print(f"Status: {r.status_code}")
        print(f"Response: {r.text[:500]}")
    except Exception as ex:
        print(f"Error: {ex}")

    print("\n=== LISTO ===")


if __name__ == "__main__":
    main()
