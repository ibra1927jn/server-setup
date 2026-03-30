"""Check certbot and dashboard status"""
from shared_config import VPS_HOST, get_ssh_client


def main():
    nip_domain = VPS_HOST.replace(".", "-") + ".nip.io"
    ssh = get_ssh_client()

    # Check Certbot status
    print('=== CERTBOT STATUS ===')
    _, o, _ = ssh.exec_command(
        f'ls -la /etc/letsencrypt/live/{nip_domain}/ 2>/dev/null || echo NO_CERT'
    )
    print(o.read().decode().strip())

    # Check Dashboard HTTP code
    print('\n=== DASHBOARD CHECK ===')
    _, o, _ = ssh.exec_command(
        f'curl -s -o /dev/null -w "%{{http_code}}" http://{VPS_HOST}/dashboard/'
    )
    print('HTTP Code:', o.read().decode().strip())

    # Check active Nginx config
    print('\n=== NGINX SSL CONFIG ===')
    _, o, _ = ssh.exec_command('grep ssl_certificate /etc/nginx/sites-available/n8n')
    print(o.read().decode().strip())

    ssh.close()


if __name__ == "__main__":
    main()
