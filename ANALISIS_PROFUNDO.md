# Análisis Profundo — set up (Scripts de Infraestructura/Deploy)
**Fecha:** 2026-03-27

---

## 1. Módulos/Sistemas Completamente Implementados

### Deploy de Crypto-Trading-Bot4 (scripts/deploy_ct4.py)
- Deploy completo via SSH/SFTP con paramiko
- Upload recursivo de ficheros al VPS Hetzner
- Filtro de directorios no necesarios (.git, venv, __pycache__, etc.)
- Límite de tamaño por fichero (>10MB se salta)

### Deploy de n8n (scripts/deploy_n8n_hetzner.py)
- Docker Compose para n8n en Hetzner VPS
- Configuración Nginx como reverse proxy
- Basic auth habilitado (admin/AgenticOS2024!)
- Volúmenes persistentes para datos de n8n

### Scripts de Diagnóstico y Fix del VPS (~100+ scripts en scripts/)
- **Diagnóstico**: check_docker_compose.py, check_exec_error.py, check_n8n_existing.py, check_n8n_logs.py, check_openrouter_balance.py, check_port_conflicts.py, check_ports.py, check_server.py, check_ssl_prereqs.py, check_webhook_paths.py
- **Fixes de n8n**: fix_n8n_cookie.py, fix_n8n_existing.py, fix_n8n_login.py, fix_n8n_proxy.py, fix_n8n_proxy2.py
- **Fixes de nginx**: fix_nginx_alias.py, fix_nginx_timeout.py, fix_dashboard_nginx.py (5 versiones)
- **Fixes de Telegram**: fix_telegram_cred.py, fix_telegram_creds.py, fix_chatid.py, fix_chat_payload.py
- **Fixes de AI agent**: fix_ai_agent_workflow.py, fix_model_and_test.py, fix_model_glm45.py, fix_import.py
- **Fixes de seguridad**: fix_ufw.py, fix_dashboard_isolation.py

### Scripts de Testing
- test.py, test_after_fix.py, test_after_restart.py, test_ai_agent.py, test_e2e_workflows.py, test_each_workflow.py, test_nginx_syntax.py, test_openrouter_direct.py, test_telegram_direct.py, test_webhook_direct.py

### Scripts de Workflow (n8n)
- Múltiples workflows JSON: crypto_alerts.json, daily_briefing.json, github_backup.json, uptime_monitor.json
- Versiones fijas de cada workflow (crypto_portfolio_alerts_fixed.json, daily_briefing_fixed.json, etc.)
- Import/export de workflows: import_workflows_hetzner.py, export_analyze_workflow.py

### Telegram Bot Scripts
- create_telegram_ai_bot.py (3 versiones)
- debug_telegram.py
- Configuración de credenciales Telegram

### Deploy de Dashboard
- deploy_chat_widget.py
- dashboard.html, dashboard_index.html
- Dashboard service configuration

### SSL
- fase3_ssl_dashboard.py — Setup de SSL con certbot
- check_ssl_prereqs.py
- mejoras_ssl_github.py

### n8n Administration
- reset_n8n_password.py (3 versiones)
- get_n8n_apikey.py
- patch_sqlite_cred.py — Parche directo de credenciales en SQLite de n8n
- query_n8n_db.py

---

## 2. Módulos a Medias o Estructura Vacía

### Todo el proyecto es scripts ad-hoc
- No hay una estructura organizada — son ~130 scripts Python sueltos en scripts/
- No hay main.py, no hay CLI, no hay interfaz unificada
- Cada script es una operación manual independiente

### Scripts de despliegue fragmentados
- Hay "fases": fase2_deploy.py, fase3_ssl_dashboard.py, final_pendientes.py
- Pero no hay un script maestro que ejecute todo en secuencia

### n8n-autostart.bat y n8n-service.ps1
- Scripts Windows para arrancar n8n localmente
- Están en scripts/ junto con scripts de VPS Linux — confusión de entornos

### Workflows duplicados
- Muchos workflows tienen 3-4 versiones: original, fixed, updated, patched
- No está claro cuál es la versión activa

---

## 3. Problemas Técnicos a Primera Vista

### CREDENCIALES EN TEXTO PLANO — CRÍTICO
- **deploy_ct4.py**: `HOST = "95.217.158.7"`, `USER = "root"`, `PASS = "tji3MtHJa9J4"`
- **deploy_n8n_hetzner.py**: misma IP y credenciales root
- `N8N_BASIC_AUTH_PASSWORD=AgenticOS2024!` en docker compose
- **Esto es una vulnerabilidad de seguridad GRAVE** — cualquiera con acceso al repo tiene acceso root al VPS

### .env_backup con secretos
- Fichero .env_backup de 16 bytes — probablemente contiene algún secreto

### Sin .gitignore efectivo
- .gitignore solo tiene 16 bytes — probablemente no cubre todos los secretos
- Los scripts con contraseñas están versionados

### SSH con paramiko y AutoAddPolicy
- `ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())` — acepta cualquier host key sin verificar
- Vulnerable a man-in-the-middle attacks

### Root login via SSH con password
- El VPS se accede como root con contraseña — la peor práctica de seguridad posible
- Debería usar SSH keys con usuario no-root + sudo

### Sin tests
- No hay tests del propio código de infraestructura
- Los "test" scripts son tests manuales del VPS, no tests del código

### Sin logging ni error handling consistente
- Cada script maneja errores de forma diferente
- Sin logging centralizado ni alertas

---

## 4. Librerías y Herramientas Exactas

### Node.js
- **ssh2 ^1.17.0** — Cliente SSH para Node.js (en package.json)

### Python (scripts/)
- **paramiko** — SSH/SFTP desde Python
- No hay requirements.txt — las dependencias no están documentadas

### Infraestructura
- **Hetzner VPS** — CX23 (2vCPU, 4GB RAM, 40GB) en IP 95.217.158.7
- **Docker / Docker Compose** — Contenedores en el VPS
- **Nginx** — Reverse proxy
- **n8n** — Plataforma de automatización (Docker image)
- **Certbot/Let's Encrypt** — SSL certificates
- **UFW** — Firewall Ubuntu

### Servicios externos referenciados
- **OpenRouter** — API de LLM (check_openrouter_balance.py)
- **Telegram Bot API** — Alertas y bot de IA
- **GitHub** — Auto-backup (github_backup.json)

---

## 5. Ficheros Más Importantes

| Fichero | Descripción |
|---------|-------------|
| `scripts/deploy_ct4.py` | Deploy del Crypto Trading Bot al VPS |
| `scripts/deploy_n8n_hetzner.py` | Deploy de n8n con Docker + Nginx |
| `scripts/fase2_deploy.py` | Fase 2 del despliegue completo |
| `scripts/fase3_ssl_dashboard.py` | Setup de SSL y dashboard |
| `scripts/create_telegram_ai_bot_v3.py` | Creación del bot de Telegram con IA |
| `scripts/daily_briefing.json` | Workflow n8n de briefing diario |
| `scripts/crypto_alerts.json` | Workflow n8n de alertas crypto |
| `scripts/uptime_monitor.json` | Workflow n8n de monitoreo uptime |
| `scripts/fix_n8n_proxy.py` | Fix del proxy nginx para n8n |
| `package.json` | Dependencia ssh2 para scripts Node |

---

## 6. Lo Que Falta Para Ser un Producto Completo

### Seguridad — URGENTE
1. **Eliminar TODAS las credenciales de los scripts** — mover a variables de entorno o vault
2. **Rotar las credenciales expuestas** — la password del VPS ya está comprometida
3. **Cambiar a SSH key authentication** — eliminar login por password
4. **Crear usuario no-root** — nunca deployar como root
5. **Habilitar fail2ban** — proteger contra brute force
6. **Verificar host keys** — no usar AutoAddPolicy

### Estructura y organización
- Crear un CLI unificado (click, typer) que agrupe todas las operaciones
- Separar scripts por función: deploy/, diagnose/, fix/, workflows/
- Eliminar scripts duplicados y versiones obsoletas
- Crear un README con inventario de operaciones disponibles

### Infrastructure as Code
- Migrar a Ansible, Terraform, o al menos scripts Bash organizados
- Docker Compose debe estar en el repo, no embebido en scripts Python
- Usar docker-compose.yml versionado con .env para secretos

### requirements.txt
- Documentar dependencias Python: paramiko, y cualquier otra

### Automatización
- CI/CD: un push a main debería deployar automáticamente
- Health checks automáticos (no scripts manuales)
- Alertas automáticas cuando algo falla

### Documentación
- Runbook de operaciones: cómo deployar, cómo diagnosticar, cómo recuperar
- Inventario de servicios corriendo en el VPS
- Diagrama de arquitectura (qué contenedores, qué puertos, qué dominos)

### Backup
- Script de backup automático de:
  - Base de datos n8n (SQLite)
  - Workflows
  - Configuración nginx
  - Datos del bot de trading

### Monitoreo
- Uptime monitoring externo (UptimeRobot, Better Stack)
- Alertas de disco lleno, RAM alta, CPU sostenido
- Log aggregation
