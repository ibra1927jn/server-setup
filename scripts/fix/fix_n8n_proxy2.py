import time

from shared_config import VPS_HOST, get_ssh_client


def main():
    ssh = get_ssh_client()

    compose_dir = "/root/n8n"
    print("Updating .env in", compose_dir)

    # Read current env
    _, o, _ = ssh.exec_command(f"cat {compose_dir}/.env")
    current_env = o.read().decode()

    # Fix settings
    lines = []
    for line in current_env.split("\\n"):
        if line.startswith("WEBHOOK_URL="):
            lines.append(f"WEBHOOK_URL=https://{VPS_HOST}/")
        elif line.startswith("N8N_PROXY_HOPS="):
            pass  # we'll add it below
        elif line.startswith("N8N_SECURE_COOKIE="):
            lines.append("N8N_SECURE_COOKIE=false")
        elif line.strip():
            lines.append(line)

    # Ensure proxy hops
    if not any("N8N_PROXY_HOPS" in line for line in lines):
        lines.append("N8N_PROXY_HOPS=1")

    new_env = "\\n".join(lines)
    print("=== NEW ENV ===")
    print(new_env)

    # Write back
    sftp = ssh.open_sftp()
    with open("/tmp/env_temp.txt", "w", encoding="utf-8") as f:
        f.write(new_env)
    sftp.put("/tmp/env_temp.txt", f"{compose_dir}/.env")
    sftp.close()

    # Restart
    print("Restarting n8n...")
    ssh.exec_command(f"cd {compose_dir} && docker-compose down && docker-compose up -d")
    time.sleep(5)

    _, o, _ = ssh.exec_command("docker logs n8n-n8n-1 --tail 10")
    print("=== DOCKER RESTART LOGS ===")
    print(o.read().decode())

    ssh.close()


if __name__ == "__main__":
    main()
