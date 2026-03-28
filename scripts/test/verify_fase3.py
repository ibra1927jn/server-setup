"""Check certbot and dashboard status"""
from shared_config import get_ssh_client

ssh = get_ssh_client()

# Check Certbot status
print('=== CERTBOT STATUS ===')
_, o, _ = ssh.exec_command('ls -la /etc/letsencrypt/live/95-217-158-7.nip.io/ 2>/dev/null || echo NO_CERT')
print(o.read().decode().strip())

# Check Dashboard HTTP code
print('\n=== DASHBOARD CHECK ===')
_, o, _ = ssh.exec_command('curl -s -o /dev/null -w "%{http_code}" http://95.217.158.7/dashboard/')
print('HTTP Code:', o.read().decode().strip())

# Check active Nginx config
print('\n=== NGINX SSL CONFIG ===')
_, o, _ = ssh.exec_command('grep ssl_certificate /etc/nginx/sites-available/n8n')
print(o.read().decode().strip())

ssh.close()
