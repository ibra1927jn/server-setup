from shared_config import get_ssh_client

ssh = get_ssh_client()

# Dump everything to a file
ssh.exec_command('docker inspect --format="{{range .Config.Env}}{{println .}}{{end}}" n8n-n8n-1 > /root/n8n_env.txt')

import time
time.sleep(2)

# Download it
sftp = ssh.open_sftp()
local_path = r'C:\Users\ibrab\Desktop\set up\scripts\n8n_env.txt'
sftp.get('/root/n8n_env.txt', local_path)
sftp.close()

ssh.close()
