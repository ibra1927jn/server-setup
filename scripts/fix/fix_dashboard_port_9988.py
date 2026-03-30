import time

from shared_config import VPS_HOST, get_ssh_client


def main():
    ssh = get_ssh_client()

    # 1. Update systemd service to use port 9988
    ssh.exec_command('sed -i "s/8081/9988/g" /etc/systemd/system/dashboard.service')
    ssh.exec_command('systemctl daemon-reload && systemctl restart dashboard')

    # 2. Update Nginx proxy port to 9988
    ssh.exec_command('sed -i "s/127.0.0.1:8081/127.0.0.1:9988/g" /etc/nginx/sites-available/n8n')
    ssh.exec_command('nginx -t && systemctl reload nginx')

    time.sleep(2)

    # Check if it works locally on the server
    print('=== LOCAL CURL DASHBOARD ===')
    _, o, _ = ssh.exec_command(f'curl -s -k -H "Host: {VPS_HOST}" http://127.0.0.1:9988/ | head -n 5')
    print(o.read().decode())

    ssh.close()


if __name__ == "__main__":
    main()
