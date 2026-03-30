from shared_config import get_ssh_client


def main():
    ssh = get_ssh_client()

    _, o, _ = ssh.exec_command('lsof -i :80')
    print('=== PORT 80 ===')
    print(o.read().decode())

    _, o, _ = ssh.exec_command('lsof -i :443')
    print('=== PORT 443 ===')
    print(o.read().decode())

    ssh.close()


if __name__ == "__main__":
    main()
