from shared_config import get_ssh_client


def main():
    ssh = get_ssh_client()

    # Get the last 50 lines of n8n logs
    _, o, _ = ssh.exec_command("docker logs n8n-n8n-1 --tail=50 2>&1")
    print(o.read().decode())

    ssh.close()


if __name__ == "__main__":
    main()
