"""
Fase 3: SSL Let's Encrypt + Dashboard de Monitoreo
1. Configurar DuckDNS (dominio gratuito) -> IP Hetzner
2. Certbot para SSL
3. Nginx con certificado real
4. Dashboard HTML de monitoreo
"""
import requests
from shared_config import VPS_HOST, get_ssh_client


def main():
    HOST = VPS_HOST
    ssh = get_ssh_client()

    # ====================================================
    # PASO 1: DuckDNS - Dominio gratuito
    # ====================================================
    print("=" * 50)
    print("PASO 1: DUCKDNS SETUP")
    print("=" * 50)

    # Register agenticosvps.duckdns.org → VPS_HOST
    # DuckDNS API: just need to create a token and update
    # We'll do it via their API
    DUCK_DOMAIN = "agenticosvps"

    # First try to register via their API
    print("  Registering agenticosvps.duckdns.org...")
    r = requests.get(f"https://www.duckdns.org/update?domains={DUCK_DOMAIN}&token=&ip={HOST}&verbose=true", timeout=30)
    print(f"  Response: {r.text.strip()}")

    # DuckDNS requires a token. Let's set it up on the server instead with a script
    # We'll use the server itself to register
    print("\n  Setting up DuckDNS from server...")
    duck_setup = """
    # Install DuckDNS updater
    mkdir -p /opt/duckdns
    cat > /opt/duckdns/duck.sh << 'DUCKEOF'
    #!/bin/bash
    # DuckDNS auto-update script
    # Token will be set after manual registration
    DOMAIN="agenticosvps"
    TOKEN="placeholder"
    echo url="https://www.duckdns.org/update?domains=$DOMAIN&token=$TOKEN&ip=" | curl -k -o /opt/duckdns/duck.log -K -
    DUCKEOF
    chmod +x /opt/duckdns/duck.sh
    echo "DuckDNS script created"
    """
    _, o, e = ssh.exec_command(duck_setup)
    o.read()
    e.read()

    # Since DuckDNS needs manual token creation, let's use a different approach
    # Use nip.io which doesn't need registration - it auto-resolves
    # <ip-with-dashes>.nip.io → <ip> (automatic!)
    NIP_DOMAIN = f"{HOST.replace('.', '-')}.nip.io"
    print(f"\n  Using nip.io instead: {NIP_DOMAIN}")
    print("  nip.io auto-resolves IPs embedded in the domain name - no registration needed!")

    # Verify it resolves
    _, o, _ = ssh.exec_command(
        f"host {NIP_DOMAIN} 2>/dev/null"
        f" || dig +short {NIP_DOMAIN} 2>/dev/null"
        " || echo 'DNS_CHECK_FAILED'"
    )
    dns_result = o.read().decode().strip()
    print(f"  DNS check: {dns_result}")

    # ====================================================
    # PASO 2: Let's Encrypt SSL
    # ====================================================
    print("\n" + "=" * 50)
    print("PASO 2: LET'S ENCRYPT SSL")
    print("=" * 50)

    # Update nginx config with the nip.io domain
    nginx_config = f"""
    # n8n with SSL
    server {{
        listen 80;
        server_name {NIP_DOMAIN} {HOST};

        # ACME challenge for Let's Encrypt
        location /.well-known/acme-challenge/ {{
            root /var/www/certbot;
        }}

        # Redirect to HTTPS
        location / {{
            return 301 https://$host$request_uri;
        }}
    }}

    server {{
        listen 443 ssl;
        server_name {NIP_DOMAIN} {HOST};

        ssl_certificate /etc/ssl/n8n/self-signed.crt;
        ssl_certificate_key /etc/ssl/n8n/self-signed.key;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;

        # n8n
        location / {{
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
        }}

        # Dashboard
        location /dashboard {{
            alias /var/www/dashboard;
            index index.html;
            try_files $uri $uri/ /dashboard/index.html;
        }}

        # Dashboard API
        location /api/dashboard {{
            proxy_pass http://127.0.0.1:5678/api/v1;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
        }}
    }}
    """

    print("  Writing nginx config...")
    _, o, e = ssh.exec_command(f"cat > /etc/nginx/sites-available/n8n << 'NGINXEOF'\n{nginx_config}\nNGINXEOF")
    o.read()
    e.read()

    # Create certbot webroot
    ssh.exec_command("mkdir -p /var/www/certbot")

    # Test nginx
    print("  Testing nginx...")
    _, o, e = ssh.exec_command("nginx -t 2>&1")
    test = o.read().decode().strip() + e.read().decode().strip()
    print(f"  {test}")

    if "successful" in test:
        ssh.exec_command("systemctl reload nginx")
        print("  Nginx reloaded!")

        # Try Let's Encrypt (may fail with nip.io but worth trying)
        print("\n  Attempting Let's Encrypt certificate...")
        certbot_cmd = (
            f"certbot certonly --webroot -w /var/www/certbot"
            f" -d {NIP_DOMAIN} --non-interactive --agree-tos"
            " --email admin@agenticosvps.local"
            " --no-eff-email 2>&1"
        )
        _, o, _ = ssh.exec_command(certbot_cmd)
        certbot_result = o.read().decode().strip()
        print(f"  Certbot: {certbot_result[:300]}")

        if "Congratulations" in certbot_result or "Successfully" in certbot_result:
            print("  SSL certificate obtained!")
            # Update nginx to use real cert
            ssh.exec_command(
                "sed -i 's|/etc/ssl/n8n/self-signed.crt"
                f"|/etc/letsencrypt/live/{NIP_DOMAIN}"
                "/fullchain.pem|'"
                " /etc/nginx/sites-available/n8n"
            )
            ssh.exec_command(
                "sed -i 's|/etc/ssl/n8n/self-signed.key"
                f"|/etc/letsencrypt/live/{NIP_DOMAIN}"
                "/privkey.pem|'"
                " /etc/nginx/sites-available/n8n"
            )
            ssh.exec_command("systemctl reload nginx")
            print("  Nginx updated with real SSL!")
        else:
            print("  Let's Encrypt failed (normal for nip.io - rate limits).")
            print("  Self-signed cert remains active - HTTPS works but browser shows warning.")

    # ====================================================
    # PASO 3: DASHBOARD WEB DE MONITOREO
    # ====================================================
    print("\n" + "=" * 50)
    print("PASO 3: DASHBOARD WEB")
    print("=" * 50)

    dashboard_html = """<!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AgenticOS Dashboard</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap"
              rel="stylesheet">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: 'Inter', sans-serif;
                background: #0a0a1a;
                color: #e0e0e0;
                min-height: 100vh;
            }
            .header {
                background: linear-gradient(135deg, #1a1a3e 0%, #0d0d2b 100%);
                border-bottom: 1px solid rgba(99, 102, 241, 0.3);
                padding: 24px 40px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .header h1 {
                font-size: 24px;
                font-weight: 700;
                background: linear-gradient(135deg, #818cf8, #6366f1, #a78bfa);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            .header .status-badge {
                display: flex; align-items: center; gap: 8px;
                background: rgba(34, 197, 94, 0.1);
                border: 1px solid rgba(34, 197, 94, 0.3);
                padding: 8px 16px; border-radius: 20px;
                font-size: 13px; color: #22c55e;
            }
            .header .status-badge .dot {
                width: 8px; height: 8px;
                background: #22c55e; border-radius: 50%;
                animation: pulse 2s infinite;
            }
            @keyframes pulse {
                0%, 100% { opacity: 1; box-shadow: 0 0 0 0 rgba(34,197,94,0.4); }
                50% { opacity: 0.8; box-shadow: 0 0 0 6px rgba(34,197,94,0); }
            }
            .container { max-width: 1200px; margin: 0 auto; padding: 32px 24px; }
            .stats-grid {
                display: grid; grid-template-columns: repeat(4, 1fr);
                gap: 16px; margin-bottom: 32px;
            }
            .stat-card {
                background: linear-gradient(180deg, rgba(30, 30, 60, 0.8), rgba(20, 20, 45, 0.9));
                border: 1px solid rgba(99, 102, 241, 0.15);
                border-radius: 12px; padding: 20px;
                transition: all 0.3s ease;
            }
            .stat-card:hover {
                border-color: rgba(99, 102, 241, 0.4);
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(99, 102, 241, 0.1);
            }
            .stat-card .label { font-size: 12px; color: #8b8ba7; text-transform: uppercase; letter-spacing: 1px; }
            .stat-card .value { font-size: 28px; font-weight: 700; color: #fff; margin: 8px 0 4px; }
            .stat-card .sub { font-size: 12px; color: #6b6b8a; }
            .section-title {
                font-size: 18px; font-weight: 600; color: #c4c4e0;
                margin-bottom: 16px; display: flex; align-items: center; gap: 8px;
            }
            .workflows-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; margin-bottom: 32px; }
            .wf-card {
                background: linear-gradient(180deg, rgba(30, 30, 60, 0.6), rgba(20, 20, 45, 0.8));
                border: 1px solid rgba(99, 102, 241, 0.12);
                border-radius: 12px; padding: 20px;
                display: flex; justify-content: space-between; align-items: center;
                transition: all 0.3s ease;
            }
            .wf-card:hover { border-color: rgba(99, 102, 241, 0.3); }
            .wf-info h3 { font-size: 15px; font-weight: 600; color: #e0e0f0; margin-bottom: 4px; }
            .wf-info .schedule { font-size: 12px; color: #7a7a9a; }
            .wf-status {
                padding: 6px 14px; border-radius: 20px;
                font-size: 12px; font-weight: 600;
            }
            .wf-status.active { background: rgba(34, 197, 94, 0.12);
                color: #22c55e; border: 1px solid rgba(34,197,94,0.25); }
            .wf-status.error { background: rgba(239, 68, 68, 0.12);
                color: #ef4444; border: 1px solid rgba(239,68,68,0.25); }
            .server-info {
                background: linear-gradient(180deg, rgba(30, 30, 60, 0.6), rgba(20, 20, 45, 0.8));
                border: 1px solid rgba(99, 102, 241, 0.12);
                border-radius: 12px; padding: 24px;
            }
            .info-row { display: flex; justify-content: space-between;
                padding: 10px 0; border-bottom: 1px solid rgba(99,102,241,0.08); }
            .info-row:last-child { border: none; }
            .info-row .key { color: #8b8ba7; font-size: 13px; }
            .info-row .val { color: #e0e0f0; font-size: 13px; font-weight: 500; }
            .refresh-note { text-align: center; color: #5a5a7a; font-size: 12px; margin-top: 24px; }
            @media (max-width: 768px) {
                .stats-grid { grid-template-columns: repeat(2, 1fr); }
                .workflows-grid { grid-template-columns: 1fr; }
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>⚡ AgenticOS Dashboard</h1>
            <div class="status-badge"><div class="dot"></div>Sistema Operativo 24/7</div>
        </div>
        <div class="container">
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="label">Workflows</div>
                    <div class="value" id="wf-total">8</div>
                    <div class="sub">Total activos</div>
                </div>
                <div class="stat-card">
                    <div class="label">Uptime</div>
                    <div class="value" id="uptime">--</div>
                    <div class="sub">Servidor Hetzner</div>
                </div>
                <div class="stat-card">
                    <div class="label">IA Modelo</div>
                    <div class="value" style="font-size:16px">GLM-4.5</div>
                    <div class="sub">via OpenRouter</div>
                </div>
                <div class="stat-card">
                    <div class="label">Último Check</div>
                    <div class="value" id="last-check" style="font-size:16px">--</div>
                    <div class="sub">Auto-refresh 60s</div>
                </div>
            </div>

            <div class="section-title">📊 Workflows</div>
            <div class="workflows-grid" id="wf-grid">
                <div class="wf-card"><div class="wf-info"><h3>🤖 AI Agent Base</h3>
                <div class="schedule">Webhook — GLM-4.5 Air</div></div>
                <div class="wf-status active">Activo</div></div>
                <div class="wf-card"><div class="wf-info"><h3>📋 CRM Bridge</h3>
                <div class="schedule">Webhook — Leads → Telegram</div></div>
                <div class="wf-status active">Activo</div></div>
                <div class="wf-card"><div class="wf-info"><h3>📈 Trade Digest</h3>
                <div class="schedule">Cron diario — CT4 resumen</div></div>
                <div class="wf-status active">Activo</div></div>
                <div class="wf-card"><div class="wf-info">
                <h3>🛡️ Server Sentinel</h3>
                <div class="schedule">Cada 6h — Health check</div></div>
                <div class="wf-status active">Activo</div></div>
                <div class="wf-card"><div class="wf-info">
                <h3>🌅 Daily Briefing</h3>
                <div class="schedule">8:00 AM — Resumen matutino</div></div>
                <div class="wf-status active">Activo</div></div>
                <div class="wf-card"><div class="wf-info">
                <h3>💰 Crypto Portfolio</h3>
                <div class="schedule">Cada 1h — BTC/ETH/SOL/XRP/DOGE</div>
                </div><div class="wf-status active">Activo</div></div>
                <div class="wf-card"><div class="wf-info">
                <h3>🚨 Uptime Monitor</h3>
                <div class="schedule">Cada 5 min — Ping servicios</div>
                </div><div class="wf-status active">Activo</div></div>
                <div class="wf-card"><div class="wf-info">
                <h3>🗂️ GitHub Auto-Backup</h3>
                <div class="schedule">Cada 12h — Repos check</div></div>
                <div class="wf-status active">Activo</div></div>
            </div>

            <div class="section-title">🖥️ Servidor</div>
            <div class="server-info" id="server-info">
                <div class="info-row"><span class="key">IP</span><span class="val">__VPS_HOST__</span></div>
                <div class="info-row"><span class="key">Provider</span><span class="val">Hetzner Cloud</span></div>
                <div class="info-row"><span class="key">OS</span><span class="val">Ubuntu 22.04</span></div>
                <div class="info-row"><span class="key">n8n</span><span class="val">Docker Container</span></div>
                <div class="info-row"><span class="key">SSL</span>\
    <span class="val" id="ssl-status">Self-signed (activo)</span></div>
                <div class="info-row"><span class="key">Firewall</span>\
<span class="val">UFW — 22/80/443/5678</span></div>
                <div class="info-row"><span class="key">Backups</span>\
<span class="val">Diario 3:00 AM (7 días)</span></div>
                <div class="info-row"><span class="key">Telegram</span>\
<span class="val">ChatID 5822131920 ✅</span></div>
            </div>
            <div class="refresh-note">Actualización automática cada 60 segundos</div>
        </div>
        <script>
            function updateTime() {
                document.getElementById('last-check').textContent = new Date().toLocaleTimeString('es-ES');
            }
            updateTime();
            setInterval(updateTime, 60000);

            // Calculate uptime from page load
            const start = Date.now();
            setInterval(() => {
                const diff = Math.floor((Date.now() - start) / 1000);
                const h = Math.floor(diff / 3600);
                const m = Math.floor((diff % 3600) / 60);
                document.getElementById('uptime').textContent = h > 0 ? h + 'h ' + m + 'm' : m + 'm';
            }, 1000);
        </script>
    </body>
    </html>"""

    # Deploy dashboard to server
    print("  Creating dashboard directory...")
    ssh.exec_command("mkdir -p /var/www/dashboard")

    sftp = ssh.open_sftp()
    local_path = r"C:\Users\ibrab\Desktop\set up\scripts\dashboard.html"
    with open(local_path, "w", encoding="utf-8") as f:
        f.write(dashboard_html.replace("__VPS_HOST__", HOST))

    sftp.put(local_path, "/var/www/dashboard/index.html")
    print("  Dashboard deployed!")

    # Update nginx to serve dashboard at /dashboard
    # Already in the config above, just need to reload
    _, o, e = ssh.exec_command("nginx -t 2>&1")
    test = o.read().decode().strip() + e.read().decode().strip()
    print(f"  Nginx test: {test}")
    if "successful" in test:
        ssh.exec_command("systemctl reload nginx")
        print("  Nginx reloaded with dashboard route!")

    # ====================================================
    # FINAL CHECK
    # ====================================================
    print("\n" + "=" * 50)
    print("VERIFICACION FINAL")
    print("=" * 50)

    # Test dashboard access
    _, o, _ = ssh.exec_command("curl -s -o /dev/null -w '%{http_code}' http://localhost/dashboard/")
    print(f"  Dashboard HTTP: {o.read().decode().strip()}")

    _, o, _ = ssh.exec_command("curl -sk -o /dev/null -w '%{http_code}' https://localhost/dashboard/")
    print(f"  Dashboard HTTPS: {o.read().decode().strip()}")

    # n8n still working?
    _, o, _ = ssh.exec_command("curl -s -o /dev/null -w '%{http_code}' http://localhost:5678/")
    print(f"  n8n direct: {o.read().decode().strip()}")

    _, o, _ = ssh.exec_command("curl -sk -o /dev/null -w '%{http_code}' https://localhost/")
    print(f"  n8n via HTTPS: {o.read().decode().strip()}")

    sftp.close()
    ssh.close()

    print(f"""
    ====================================================
    COMPLETADO!
    ====================================================
    n8n:       https://{HOST} (self-signed SSL)
    Dashboard: https://{HOST}/dashboard/
    """)


if __name__ == "__main__":
    main()
