from shared_config import get_ssh_client


def main():
    ssh = get_ssh_client()

    _, o, _ = ssh.exec_command("systemctl is-active nginx")
    print("NGINX STATUS:", o.read().decode().strip())

    _, o, _ = ssh.exec_command("ss -tlnp | grep 443")
    print("PORT 443 BINDINGS:", o.read().decode())

    ssh.close()


if __name__ == "__main__":
    main()
