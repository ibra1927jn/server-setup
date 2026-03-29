# set up — Server automation and infrastructure management for Hetzner VPS

## Stack
- Python 3 (paramiko, requests, python-dotenv)
- Node.js (ssh2)
- n8n (Docker on Hetzner VPS) + Nginx + UFW + Certbot
- mission-control/ — React 19 + Vite 8 dashboard (separate sub-project)

## Commands
```bash
python scripts/deploy/deploy_n8n_hetzner.py   # Deploy n8n with Docker + Nginx
python scripts/deploy/fase2_deploy.py          # Firewall + import workflows
python scripts/deploy/fase3_ssl_dashboard.py   # SSL + dashboard
python scripts/deploy/deploy_ct4.py            # Deploy CT4 bot to Hetzner
python scripts/diagnostics/check_server.py     # VPS diagnostics
cd mission-control && npm run dev              # Dashboard dev server
```

## Architecture
```
scripts/
├── shared_config.py      # Centralized config (loads .env via python-dotenv)
├── deploy/               # 5 deploy scripts (n8n, CT4, SSL, phases)
├── diagnostics/          # 13 scripts (check_*, diag_*, inspect_*)
├── fix/                  # 23 scripts (fix_*, migrate_ssh_keys.sh)
├── test/                 # 16 scripts (test_*, verify_*, minimal_test)
├── workflows/            # 7 n8n workflow JSONs (update_* + patches)
└── (root)                # Telegram bots, dashboard.html, utilities
mission-control/          # React dashboard (see its own CLAUDE.md)
```

## Environment variables (key names only, defined in scripts/.env)
VPS_HOST, VPS_USER, VPS_PASS, VPS_SSH_KEY_PATH,
N8N_URL, N8N_EMAIL, N8N_PASSWORD, N8N_API_KEY,
TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID,
OPENROUTER_API_KEY, GITHUB_PAT

## Project rules
- Credentials centralized in shared_config.py + .env (never commit .env)
- Workflow: check -> fix -> test -> repeat
- Code in English, comments in Spanish
- Commits in English, format: type(scope): short description
- Read ERRORES.md before starting any task
- Update PROGRESS.md when a task is completed

## n8n workflows (active on VPS)
Daily Briefing (8 AM), Uptime Monitor (5 min), Crypto Portfolio Alerts (1h),
GitHub Auto-Backup (12h), Telegram AI Bot (webhook)

## Current state
- Credentials migrated from hardcoded to shared_config.py + .env
- Scripts organized into subdirectories (deploy, diagnostics, fix, test, workflows)
- ~35 duplicate/dead files cleaned up (2026-03-28)
- Pending: migrate VPS auth from password to SSH keys
- No formal test suite (pytest not configured yet)
