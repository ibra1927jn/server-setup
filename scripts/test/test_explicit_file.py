from shared_config import get_ssh_client

ssh = get_ssh_client()

print('=== NGINX RESTART FOR CLEAN STATE ===')
ssh.exec_command('systemctl restart nginx')
import time
time.sleep(2)

print('=== EXPLICIT FILE REQUEST ===')
_, o, _ = ssh.exec_command('curl -s -k -H "Host: 95.217.158.7" https://localhost/status_panel/index.html | head -n 5')
print(o.read().decode())

print('=== NGINX ERROR LOG ===')
_, o, _ = ssh.exec_command('tail -n 10 /var/log/nginx/error.log')
print(o.read().decode())

ssh.close()
