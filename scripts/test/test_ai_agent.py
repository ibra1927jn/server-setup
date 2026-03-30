"""Activate all workflows and test the AI Agent webhook"""
import requests
from shared_config import VPS_HOST, get_ssh_client


def main():
    print("--- Connecting to Hetzner ---")
    ssh = get_ssh_client()

    print("--- Activating all workflows ---")
    activate_cmd = "docker exec n8n-n8n-1 n8n update:workflow --all --active=true"
    _, o, e = ssh.exec_command(activate_cmd)
    print("Out:", o.read().decode().strip())
    err = e.read().decode().strip()
    if err:
        print("Err:", err)

    print("--- Current Workflows ---")
    _, o, _ = ssh.exec_command("docker exec n8n-n8n-1 n8n list:workflow")
    print(o.read().decode().strip())

    ssh.close()

    print("\n--- Testing AI Agent Webhook ---")
    webhook_url = f"http://{VPS_HOST}:5678/webhook/ai-agent"
    payload = {
        "chatInput": "Hello from AgenticOS Production Engine! Can you confirm you are online and powered by GLM-4?"
    }
    print(f"Sending POST request to {webhook_url}...")
    try:
        response = requests.post(webhook_url, json=payload, timeout=30)
        print("Status Code:", response.status_code)
        try:
            print("Response JSON:", response.json())
        except Exception:
            print("Response Text:", response.text)
    except Exception as e:
        print("Request failed:", e)


if __name__ == "__main__":
    main()
