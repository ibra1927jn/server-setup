from shared_config import VPS_HOST, get_ssh_client


def main():
    ssh = get_ssh_client()

    # Test the webhook directly from the server
    cmd = f"""curl -s -k -X POST https://127.0.0.1/webhook/ai-agent \
      -H "Content-Type: application/json" \
      -H "Host: {VPS_HOST}" \
      -d '{{"message": "Hola, di simplemente OK"}}' """

    _, o, e = ssh.exec_command(cmd)
    print("=== WEBHOOK RESPONSE ===")
    print(o.read().decode())
    print("STDERR:", e.read().decode())

    # Also check recent execution errors
    _, o2, _ = ssh.exec_command("docker logs n8n-n8n-1 --tail=30 2>&1 | grep -i 'error\\|fail\\|warn'")
    print("\n=== RECENT N8N ERRORS ===")
    print(o2.read().decode())

    ssh.close()


if __name__ == "__main__":
    main()
