from shared_config import get_ssh_client

ssh = get_ssh_client()

sftp = ssh.open_sftp()
local_path = r'C:\Users\ibrab\Desktop\set up\scripts\dashboard_index.html'
sftp.get('/var/www/dashboard/index.html', local_path)
sftp.close()
ssh.close()
