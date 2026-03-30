from shared_config import get_ssh_client

ssh = get_ssh_client()

# Rename the folder just to be safe
ssh.exec_command('mv /var/www/dashboard /var/www/status_panel')

nginx_config = """server {
    listen 80;
    server_name 95-217-158-7.nip.io 95.217.158.7;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl;
    server_name 95-217-158-7.nip.io 95.217.158.7;

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

    # NEW URL FOR DASHBOARD
    location /status_panel/ {
        alias /var/www/status_panel/;
        index index.html;
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
"""

sftp = ssh.open_sftp()
local_path = r'C:\Users\ibrab\Desktop\set up\scripts\temp_nginx5'
with open(local_path, 'w', encoding='utf-8') as f:
    f.write(nginx_config)
sftp.put(local_path, '/etc/nginx/sites-available/n8n')
sftp.close()

_, o, e = ssh.exec_command('nginx -t && systemctl reload nginx')
print('NGINX:', o.read().decode())

_, o, _ = ssh.exec_command('curl -s -k -H "Host: 95.217.158.7" https://127.0.0.1/status_panel/ | head -n 5')
print('=== STATUS PANEL HTML ===')
print(o.read().decode())

ssh.close()
