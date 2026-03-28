# set up — Automatizacion de servidor e infraestructura

## Stack
Python 3 (paramiko para SSH/SFTP) + Node.js (ssh2)
n8n (Docker en Hetzner VPS) + Nginx + UFW + Certbot
Scripts ad-hoc para deploy, diagnostico y reparacion

## Comandos
- `python scripts/deploy/deploy_n8n_hetzner.py` — Deploy n8n con Docker + Nginx
- `python scripts/deploy/fase2_deploy.py` — Firewall + importar workflows
- `python scripts/deploy/fase3_ssl_dashboard.py` — SSL + dashboard
- `python scripts/deploy/deploy_ct4.py` — Deploy CT4 bot a Hetzner
- `python scripts/diagnostics/check_server.py` — Diagnostico del VPS
- `pytest` — No hay tests formales (pendiente)

## Estructura clave
- scripts/ — Scripts Python organizados por funcion
  - shared_config.py — Configuracion centralizada (carga .env)
  - .env — Variables de entorno (NO commitear)
  - deploy/ — deploy_*.py, fase*_deploy.py (5 scripts)
  - diagnostics/ — check_*.py, diag_*.py, inspect_*.py (13 scripts)
  - fix/ — fix_*.py (21 scripts)
  - test/ — test_*.py, verify_*.py (16 scripts)
  - workflows/ — *.json (7 archivos, solo versiones update_*)
  - (root) — Utilidades sueltas, bots telegram, dashboard.html
- package.json — Solo ssh2 como dependencia Node

## Reglas del proyecto
- Credenciales centralizadas en shared_config.py + .env (ya migrado)
  - Nunca commitear .env ni credenciales nuevas
- requirements.txt presente (paramiko, requests, python-dotenv)
- Scripts organizados en subdirectorios por funcion
- Flujo manual: check -> fix -> test -> repeat
- VPS Hetzner: 95.217.158.7 (root, password auth — migrar a SSH keys)

## Workflows n8n activos
- Daily Briefing (8 AM)
- Uptime Monitor (cada 5 min)
- Crypto Portfolio Alerts (cada 1 hora)
- GitHub Auto-Backup (cada 12 horas)
- Telegram AI Bot (webhook trigger)
