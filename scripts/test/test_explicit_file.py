import time

from shared_config import VPS_HOST, get_ssh_client


def main():
    ssh = get_ssh_client()

    print('=== NGINX RESTART FOR CLEAN STATE ===')
    ssh.exec_command('systemctl restart nginx')
    time.sleep(2)

    print('=== EXPLICIT FILE REQUEST ===')
    curl_cmd = (
        f'curl -s -k -H "Host: {VPS_HOST}"'
        ' https://localhost/status_panel/index.html | head -n 5'
    )
    _, o, _ = ssh.exec_command(curl_cmd)
    print(o.read().decode())

    print('=== NGINX ERROR LOG ===')
    _, o, _ = ssh.exec_command('tail -n 10 /var/log/nginx/error.log')
    print(o.read().decode())

    ssh.close()


if __name__ == "__main__":
    main()
