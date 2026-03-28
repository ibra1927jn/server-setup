from shared_config import get_ssh_client

ssh = get_ssh_client()

_, o, e = ssh.exec_command('nginx -t')
print('=== NGINX TEST ===')
print(o.read().decode())
print(e.read().decode())

_, o, _ = ssh.exec_command('journalctl -u nginx --no-pager | tail -n 20')
print('=== NGINX LOGS ===')
print(o.read().decode())

ssh.close()
