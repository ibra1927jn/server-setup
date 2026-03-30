"""Script to fix Nginx dashboard routing"""
from shared_config import get_ssh_client

ssh = get_ssh_client()

# Read the current config
_, o, _ = ssh.exec_command('cat /etc/nginx/sites-available/n8n')
config = o.read().decode()

# Replace the dashboard block with a correct alias/root block
# Using `root /var/www;` instead of `alias` is safer for this mapping
new_config = config.replace(
    '''    # Dashboard
    location /dashboard {
        alias /var/www/dashboard;
        index index.html;
        try_files $uri $uri/ /dashboard/index.html;
    }''',
    '''    # Dashboard
    location /dashboard/ {
        alias /var/www/dashboard/;
        index index.html;
        try_files $uri $uri/ =404;
    }

    # Exact match for /dashboard without trailing slash
    location = /dashboard {
        return 301 /dashboard/;
    }'''
)

# Replace the file content
update_script = f"""
cat > /etc/nginx/sites-available/n8n << 'EOF'
{new_config}EOF
nginx -t && systemctl reload nginx
"""

_, o, e = ssh.exec_command(update_script)
print("OUT:", o.read().decode())
print("ERR:", e.read().decode())

# Test it again
print("\n=== LOCAL CURL DASHBOARD ===")
_, o, _ = ssh.exec_command('curl -s -k https://localhost/dashboard/ | head -n 5')
print(o.read().decode())

ssh.close()
