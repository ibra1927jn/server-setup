from shared_config import get_ssh_client

ssh = get_ssh_client()

print("Executing workflow...")
_, ex_o, ex_e = ssh.exec_command('docker exec n8n-n8n-1 n8n execute --id O5sU2uD0f5SngbIu')
print("OUTPUT:")
print(ex_o.read().decode())
print("ERROR:")
print(ex_e.read().decode())

ssh.close()
