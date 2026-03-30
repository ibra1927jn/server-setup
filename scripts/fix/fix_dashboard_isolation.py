import time

from shared_config import VPS_HOST, get_ssh_client

_NIP_HOST = VPS_HOST.replace(".", "-") + ".nip.io"


def _build_systemd_service():
    """Build the systemd unit file for the dashboard HTTP server."""
    return """[Unit]
Description=Dashboard HTTP Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/var/www/status_panel
ExecStart=/usr/bin/python3 -m http.server 8080
Restart=on-failure

[Install]
WantedBy=multi-user.target
"""


def _build_nginx_config():
    """Build the nginx config with dashboard proxy and n8n routes."""
    return """server {
    listen 80;
    server_name __NIP__ __VPS__;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl;
    server_name __NIP__ __VPS__;

    ssl_certificate /etc/ssl/n8n/self-signed.crt;
    ssl_certificate_key /etc/ssl/n8n/self-signed.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Dashboard API
    location /api/dashboard/ {
        proxy_pass http://127.0.0.1:5678/api/v1/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }

    # Proxy dashboard to python server
    location /dashboard/ {
        proxy_pass http://127.0.0.1:8080/;
        proxy_set_header Host $host;
    }

    # Redirect /dashboard to /dashboard/
    location = /dashboard {
        return 301 /dashboard/;
    }

    # n8n App
    location / {
        proxy_pass http://127.0.0.1:5678;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
""".replace("__NIP__", _NIP_HOST).replace("__VPS__", VPS_HOST)


def main():
    ssh = get_ssh_client()

    sftp = ssh.open_sftp()
    local_path = "/tmp/dashboard_service"
    with open(local_path, "w", encoding="utf-8") as f:
        f.write(_build_systemd_service())
    sftp.put(local_path, "/etc/systemd/system/dashboard.service")
    sftp.close()

    ssh.exec_command("systemctl daemon-reload")
    ssh.exec_command("systemctl enable dashboard")
    ssh.exec_command("systemctl restart dashboard")

    sftp = ssh.open_sftp()
    local_path = "/tmp/temp_nginx6"
    with open(local_path, "w", encoding="utf-8") as f:
        f.write(_build_nginx_config())
    sftp.put(local_path, "/etc/nginx/sites-available/n8n")
    sftp.close()

    ssh.exec_command("mv /var/www/status_panel /var/www/dashboard")
    ssh.exec_command('sed -i "s/status_panel/dashboard/g" /etc/systemd/system/dashboard.service')
    ssh.exec_command("systemctl daemon-reload && systemctl restart dashboard")
    ssh.exec_command("nginx -t && systemctl reload nginx")

    time.sleep(3)

    print("=== LOCAL CURL DASHBOARD ===")
    _, o, _ = ssh.exec_command(f'curl -s -k -H "Host: {VPS_HOST}" https://localhost/dashboard/ | head -n 5')
    print(o.read().decode())

    ssh.close()


if __name__ == "__main__":
    main()
