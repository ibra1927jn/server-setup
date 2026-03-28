from shared_config import get_ssh_client

ssh = get_ssh_client()

_, o, _ = ssh.exec_command('ps -f -p $(lsof -t -i :80)')
print('=== ROGUE PROCESS INFO ===')
print(o.read().decode())

ssh.exec_command('kill -9 $(lsof -t -i :80)')
ssh.exec_command('systemctl start nginx')

_, o, _ = ssh.exec_command('systemctl is-active nginx')
print('=== NGINX STATUS ===')
print(o.read().decode().strip())

ssh.close()
