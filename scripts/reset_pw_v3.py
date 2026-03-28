import time
from shared_config import get_ssh_client, N8N_EMAIL, N8N_PASSWORD

ssh = get_ssh_client()

# Crear script remoto inyectando la password desde shared_config
# Se usa .replace() para evitar conflictos con f-strings del script remoto
reset_script_template = '''
import subprocess, json

# Generate bcrypt hash inside the container
result = subprocess.run(
    ["docker", "exec", "n8n-n8n-1", "node", "-e",
     "const b=require('/usr/local/lib/node_modules/n8n/node_modules/.pnpm/bcryptjs@2.4.3/node_modules/bcryptjs');b.hash('__N8N_PW__',10,(e,h)=>{console.log(h)})"],
    capture_output=True, text=True
)
pw_hash = result.stdout.strip()
print(f"Hash: {pw_hash}")

if pw_hash and pw_hash.startswith("$2"):
    # Write a SQL file to avoid shell escaping issues
    sql = f"UPDATE user SET password = '{pw_hash}';"
    with open("/tmp/update_pw.sql", "w") as f:
        f.write(sql)

    # Execute it
    vol = "/var/lib/docker/volumes/n8n_data/_data"
    r2 = subprocess.run(["sqlite3", f"{vol}/database.sqlite", f".read /tmp/update_pw.sql"],
                        capture_output=True, text=True)
    print(f"Update stdout: {r2.stdout}")
    print(f"Update stderr: {r2.stderr}")

    # Verify
    r3 = subprocess.run(["sqlite3", f"{vol}/database.sqlite", "SELECT email, substr(password,1,20) FROM user;"],
                        capture_output=True, text=True)
    print(f"Verify: {r3.stdout}")
else:
    print("Failed to generate hash")
    print(f"stderr: {result.stderr}")
'''

# Inyectar credenciales reales
reset_script = reset_script_template.replace('__N8N_PW__', N8N_PASSWORD)

with ssh.open_sftp() as sftp:
    with sftp.file('/tmp/reset_pw.py', 'w') as f:
        f.write(reset_script)

time.sleep(1)
_, o, e = ssh.exec_command("python3 /tmp/reset_pw.py")
time.sleep(10)
print("STDOUT:", o.read().decode())
print("STDERR:", e.read().decode())

# Now test login
time.sleep(1)
login_cmd = f'''curl -s -X POST http://127.0.0.1:5678/rest/login \
  -H "Content-Type: application/json" \
  -d '{{"emailOrLdapLoginId":"{N8N_EMAIL}","password":"{N8N_PASSWORD}"}}' '''
_, o2, _ = ssh.exec_command(login_cmd)
time.sleep(3)
print("\n=== LOGIN TEST ===")
print(o2.read().decode()[:300])

ssh.close()
