import time
from shared_config import get_ssh_client, N8N_PASSWORD

ssh = get_ssh_client()

# Use Node.js inside the container to hash a new password and update the database
# n8n uses bcrypt for password hashing
node_script = f"""
const {{ compare, hash }} = require('bcryptjs');
const Database = require('better-sqlite3');

async function resetPassword() {{
  const newPassword = '{N8N_PASSWORD}';
  const hashedPassword = await hash(newPassword, 10);

  const db = new Database('/home/node/.n8n/database.sqlite');
  const users = db.prepare('SELECT id, email FROM user').all();
  console.log('Users found:', JSON.stringify(users));

  if (users.length > 0) {{
    const stmt = db.prepare('UPDATE user SET password = ? WHERE id = ?');
    stmt.run(hashedPassword, users[0].id);
    console.log('Password updated for user:', users[0].email);
    console.log('Password reset complete.');
  }}
  db.close();
}}

resetPassword().catch(e => console.error('Error:', e.message));
"""

# Write the script to container
with ssh.open_sftp() as sftp:
    with sftp.file('/tmp/reset_pw.js', 'w') as f:
        f.write(node_script)

time.sleep(1)
ssh.exec_command("docker cp /tmp/reset_pw.js n8n-n8n-1:/tmp/reset_pw.js")
time.sleep(1)

_, o, e = ssh.exec_command("docker exec n8n-n8n-1 node /tmp/reset_pw.js")
time.sleep(5)
print("STDOUT:", o.read().decode())
print("STDERR:", e.read().decode())

ssh.close()
