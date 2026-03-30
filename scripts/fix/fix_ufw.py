from shared_config import get_ssh_client


def main():
    ssh = get_ssh_client()

    ssh.exec_command("ufw allow 80/tcp")
    ssh.exec_command("ufw allow 443/tcp")

    _, o, _ = ssh.exec_command('ss -tlnp | grep -E "(80|443|5678)"')
    print(o.read().decode())
    ssh.close()


if __name__ == "__main__":
    main()
