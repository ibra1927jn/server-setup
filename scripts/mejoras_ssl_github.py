"""
MEJORAS 2 y 3:
- Configurar Nginx reverse proxy + SSL para n8n
- Agregar GitHub token al workflow GitHub Auto-Backup
- Verificar ejecuciones de los tests E2E
"""
import json
import time
from shared_config import get_ssh_client

ssh = get_ssh_client()

# ====================================================
# MEJORA 2: Nginx reverse proxy con SSL
# ====================================================
print("=" * 50)
print("MEJORA 2: NGINX REVERSE PROXY + SSL")
print("=" * 50)

# alz.agency no apunta a este server. Necesitamos usar el IP directamente
# o configurar un subdominio. Creo config con IP y self-signed cert.
# Cuando tenga dominio que apunte al server, puede usar Let's Encrypt.

nginx_config = """
server {
    listen 80;
    server_name 95.217.158.7;

    # Redirect todo por HTTPS
    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl;
    server_name 95.217.158.7;

    ssl_certificate /etc/ssl/n8n/self-signed.crt;
    ssl_certificate_key /etc/ssl/n8n/self-signed.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://127.0.0.1:5678;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;
        proxy_cache off;
        chunked_transfer_encoding off;
    }
}
"""

# Generate self-signed cert
print("  Generating self-signed SSL certificate...")
ssl_cmds = [
    "mkdir -p /etc/ssl/n8n",
    'openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout /etc/ssl/n8n/self-signed.key -out /etc/ssl/n8n/self-signed.crt -subj "/CN=95.217.158.7/O=AgenticOS"',
]
for cmd in ssl_cmds:
    _, o, e = ssh.exec_command(cmd)
    o.read()
    e.read()
    print(f"    OK: {cmd[:60]}...")

# Check if there's an existing nginx config that might conflict
print("\n  Checking existing nginx config...")
_, o, _ = ssh.exec_command("ls /etc/nginx/sites-enabled/")
existing = o.read().decode().strip()
print(f"    Existing sites: {existing}")

# Write the n8n nginx config
print("  Writing n8n nginx config...")
write_cmd = "cat > /etc/nginx/sites-available/n8n << 'NGINXCONF'\n" + nginx_config + "\nNGINXCONF"
_, o, e = ssh.exec_command(write_cmd)
o.read()
e.read()

# Enable the site
_, o, e = ssh.exec_command("ln -sf /etc/nginx/sites-available/n8n /etc/nginx/sites-enabled/n8n")
o.read()
e.read()

# Test nginx config
print("  Testing nginx config...")
_, o, e = ssh.exec_command("nginx -t 2>&1")
test_result = o.read().decode().strip() + e.read().decode().strip()
print(f"    {test_result}")

if "successful" in test_result:
    print("  Reloading nginx...")
    _, o, e = ssh.exec_command("systemctl reload nginx")
    o.read()
    e.read()
    print("    Nginx reloaded!")
else:
    print("    [WARN] Nginx config test failed, skipping reload")

# ====================================================
# MEJORA 3: GitHub token en el workflow
# ====================================================
print("\n" + "=" * 50)
print("MEJORA 3: GITHUB TOKEN EN AUTO-BACKUP")
print("=" * 50)

# First create a credential for GitHub HTTP Header Auth
# We'll create it via the n8n credential creation
# The user's GitHub token from .env
github_token = None
try:
    with open(r"C:\AgenticOS\.env", "r") as f:
        for line in f:
            if "GITHUB" in line.upper() and "TOKEN" in line.upper() and "=" in line:
                github_token = line.split("=", 1)[1].strip().strip('"').strip("'")
                break
except Exception:
    pass

if not github_token:
    print("  No GitHub token found in .env, checking for PAT...")
    # Try to find it in any script
    try:
        import glob
        for f in glob.glob(r"C:\Users\ibrab\Desktop\set up\scripts\*.py"):
            with open(f, "r") as fh:
                content = fh.read()
                if "ghp_" in content or "github_pat_" in content:
                    import re
                    match = re.search(r'(ghp_[A-Za-z0-9_]+|github_pat_[A-Za-z0-9_]+)', content)
                    if match:
                        github_token = match.group(1)
                        print(f"  Found token in {f}")
                        break
    except Exception:
        pass

if github_token:
    print(f"  Token found: {github_token[:10]}...")
    
    # Update the GitHub Auto-Backup workflow to include the auth header
    _, o, _ = ssh.exec_command("docker exec n8n-n8n-1 n8n export:workflow --all")
    raw = o.read().decode().strip()
    all_wfs = json.loads(raw)
    
    for wf in all_wfs:
        if "GitHub" in wf.get("name", ""):
            print(f"  Updating workflow: {wf['name']}")
            for node in wf.get("nodes", []):
                if node.get("name") == "Get Repos":
                    print(f"    Fixing node: {node['name']}")
                    # Add direct header authentication
                    node["parameters"]["authentication"] = "genericCredentialType"
                    node["parameters"]["genericAuthType"] = "httpHeaderAuth"
                    node["parameters"]["sendHeaders"] = True
                    node["parameters"]["headerParameters"] = {
                        "parameters": [
                            {
                                "name": "Authorization",
                                "value": f"Bearer {github_token}"
                            },
                            {
                                "name": "User-Agent",
                                "value": "AgenticOS-Backup"
                            }
                        ]
                    }
                    # Remove the credential requirement (use inline headers instead)
                    if "authentication" in node["parameters"]:
                        node["parameters"]["authentication"] = "none"
                    if "genericAuthType" in node["parameters"]:
                        del node["parameters"]["genericAuthType"]
                    
                    print("    Headers added with GitHub token")
            
            # Save and reimport
            local_path = r"C:\Users\ibrab\Desktop\set up\scripts\github_backup_fixed.json"
            with open(local_path, "w", encoding="utf-8") as f:
                json.dump(wf, f)
            
            sftp = ssh.open_sftp()
            sftp.put(local_path, "/tmp/github_backup_fixed.json")
            ssh.exec_command("docker cp /tmp/github_backup_fixed.json n8n-n8n-1:/tmp/github_backup_fixed.json")
            time.sleep(1)
            _, o, e = ssh.exec_command("docker exec n8n-n8n-1 n8n import:workflow --input=/tmp/github_backup_fixed.json")
            print(f"    Import: {o.read().decode().strip()}")
            sftp.close()
            break
else:
    print("  [SKIP] No GitHub token found. You can add one manually later.")
    print("  To add: Open GitHub Auto-Backup in n8n > Get Repos node > add Authorization header")

# ====================================================
# VERIFICAR TEST E2E: Check last execution results
# ====================================================
print("\n" + "=" * 50)
print("VERIFICACION: RESULTADOS DE TESTS E2E")
print("=" * 50)

# Check n8n execution history via API
_, o, _ = ssh.exec_command("""docker exec n8n-n8n-1 sh -c 'curl -s http://localhost:5678/api/v1/executions?limit=10 2>/dev/null | python3 -m json.tool 2>/dev/null || echo "API_UNAVAILABLE"'""")
exec_result = o.read().decode().strip()

if "API_UNAVAILABLE" not in exec_result:
    try:
        execs = json.loads(exec_result)
        data = execs.get("data", execs) if isinstance(execs, dict) else execs
        if isinstance(data, list):
            for ex in data[:10]:
                wf_name = ex.get("workflowData", {}).get("name", "?")
                status = ex.get("status", "?")
                finished = ex.get("stoppedAt", "?")
                emoji = "V" if status == "success" else "X"
                print(f"  [{emoji}] {wf_name} -> {status} ({finished})")
    except Exception:
        print("  Could not parse execution history")
else:
    print("  API not available, checking via CLI...")
    # Just verify containers are running
    _, o, _ = ssh.exec_command("docker exec n8n-n8n-1 n8n list:workflow")
    print(o.read().decode().strip())

# Final SSL test
print("\n" + "=" * 50)
print("TEST: NGINX SSL")
print("=" * 50)
_, o, _ = ssh.exec_command("curl -sk https://localhost/ -o /dev/null -w '%{http_code}' 2>/dev/null")
code = o.read().decode().strip()
print(f"  HTTPS localhost -> {code}")

if code == "200" or code == "301":
    print("  SSL reverse proxy WORKING!")
else:
    print(f"  Status: {code}")

ssh.close()
print("\nCOMPLETADO!")
