from shared_config import get_ssh_client


def main():
    ssh = get_ssh_client()

    _, o, _ = ssh.exec_command('tail -n 20 /var/log/nginx/error.log | grep -i bind')
    print('=== NGINX BIND ERRORS ===')
    print(o.read().decode())
    ssh.close()


if __name__ == "__main__":
    main()
