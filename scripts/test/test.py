from shared_config import VPS_HOST, get_ssh_client


def main():
    ssh = get_ssh_client()

    _, o, _ = ssh.exec_command(
        f'curl -s -k -H "Host: {VPS_HOST}" https://localhost/dashboard/ | head -n 5'
    )
    print('=== CURL ===')
    print(o.read().decode())

    _, o, _ = ssh.exec_command('tail -n 10 /var/log/nginx/access.log | grep dashboard')
    print('=== NGINX LOG ===')
    print(o.read().decode())

    ssh.close()


if __name__ == "__main__":
    main()
