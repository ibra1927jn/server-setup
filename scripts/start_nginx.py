from shared_config import get_ssh_client

ssh = get_ssh_client()

ssh.exec_command('systemctl start nginx')
import time
time.sleep(1)

_, o, _ = ssh.exec_command('journalctl -u nginx --no-pager | tail -n 20')
print(o.read().decode())
ssh.close()
