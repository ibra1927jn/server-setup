from shared_config import get_ssh_client

ssh = get_ssh_client()

_, o, _ = ssh.exec_command('curl -s -k -H "Host: 95.217.158.7" https://localhost/dashboard/ | head -n 5')
print('=== CURL ===')
print(o.read().decode())

_, o, _ = ssh.exec_command('tail -n 10 /var/log/nginx/access.log | grep dashboard')
print('=== NGINX LOG ===')
print(o.read().decode())

ssh.close()
