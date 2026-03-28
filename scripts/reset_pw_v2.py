import time
from shared_config import get_ssh_client, N8N_EMAIL, N8N_PASSWORD

ssh = get_ssh_client()

# Install sqlite3 CLI in the container and use bcrypt from n8n's modules
# Step 1: Generate bcrypt hash using n8n's bcryptjs
hash_script = f"""
const bcrypt = require('/usr/local/lib/node_modules/n8n/node_modules/.pnpm/bcryptjs@2.4.3/node_modules/bcryptjs');
bcrypt.hash('{N8N_PASSWORD}', 10, function(err, hash) {{
  if (err) {{ console.error(err); return; }}
  console.log('HASH:' + hash);
}});
"""

with ssh.open_sftp() as sftp:
    with sftp.file('/tmp/gen_hash.js', 'w') as f:
        f.write(hash_script)

time.sleep(1)
ssh.exec_command("docker cp /tmp/gen_hash.js n8n-n8n-1:/tmp/gen_hash.js")
time.sleep(1)

_, o, e = ssh.exec_command("docker exec n8n-n8n-1 node /tmp/gen_hash.js")
time.sleep(3)
output = o.read().decode().strip()
print("OUTPUT:", output)

if 'HASH:' in output:
    password_hash = output.split('HASH:')[1].strip()
    print("Generated hash:", password_hash)
    
    # Step 2: Use the n8n volume to directly modify the SQLite DB
    # Install sqlite3 on the host and access the volume
    ssh.exec_command("apt-get install -y sqlite3 2>/dev/null")
    time.sleep(5)
    
    # Find the volume path
    _, o2, _ = ssh.exec_command("docker volume inspect n8n_data --format '{{.Mountpoint}}'")
    time.sleep(1)
    volume_path = o2.read().decode().strip()
    print("Volume path:", volume_path)
    
    # Update the password directly
    escaped_hash = password_hash.replace("$", "\\$")
    update_cmd = f'''sqlite3 {volume_path}/database.sqlite "UPDATE user SET password = '{password_hash}' WHERE 1=1;"'''
    _, o3, e3 = ssh.exec_command(update_cmd)
    time.sleep(2)
    print("UPDATE STDOUT:", o3.read().decode())
    print("UPDATE STDERR:", e3.read().decode())
    
    # Verify login
    time.sleep(1)
    login_cmd = f'''curl -s -X POST http://127.0.0.1:5678/rest/login \
      -H "Content-Type: application/json" \
      -d '{{"emailOrLdapLoginId":"{N8N_EMAIL}","password":"{N8N_PASSWORD}"}}'  '''
    _, o4, _ = ssh.exec_command(login_cmd)
    time.sleep(3)
    login_result = o4.read().decode()
    print("\n=== LOGIN TEST ===")
    print(login_result[:300])

ssh.close()
