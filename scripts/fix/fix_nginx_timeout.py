import time

from shared_config import get_ssh_client


def main():
    ssh = get_ssh_client()

    # Increase Nginx proxy timeouts
    _, o, _ = ssh.exec_command("cat /etc/nginx/sites-available/n8n")
    nginx_conf = o.read().decode()
    print("=== CURRENT NGINX CONF ===")
    print(nginx_conf)

    # Add proxy timeout settings if not present
    if 'proxy_read_timeout' not in nginx_conf:
        nginx_conf = nginx_conf.replace(
            'proxy_set_header Connection "upgrade";',
            'proxy_set_header Connection "upgrade";\n'
            '        proxy_read_timeout 120s;\n'
            '        proxy_connect_timeout 120s;\n'
            '        proxy_send_timeout 120s;'
        )

        with ssh.open_sftp() as sftp:
            with sftp.file('/etc/nginx/sites-available/n8n', 'w') as f:
                f.write(nginx_conf)

        _, o, e = ssh.exec_command("nginx -t")
        print("NGINX TEST:", e.read().decode())

        ssh.exec_command("systemctl reload nginx")
        time.sleep(2)
        print("Nginx reloaded with 120s timeout")

    # Now test directly against n8n port (bypass nginx)
    print("\n=== TESTING DIRECTLY ON PORT 5678 ===")
    cmd = '''curl -s -X POST http://127.0.0.1:5678/webhook/ai-agent \
      -H "Content-Type: application/json" \
      -d '{"chatInput": "Di OK"}' --max-time 60'''
    _, o2, e2 = ssh.exec_command(cmd)
    time.sleep(30)
    print("RESPONSE:", o2.read().decode())
    print("ERROR:", e2.read().decode())

    ssh.close()


if __name__ == "__main__":
    main()
