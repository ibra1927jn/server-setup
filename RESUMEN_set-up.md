# RESUMEN: set up (n8n Workflow Scripts)

**Stack:** Node.js (ssh2), JSON workflows para n8n
**Última modificación:** Mar 26, 2026

## Descripción
Colección de workflows n8n para automatización del servidor y vida personal. Incluye scripts para importar/actualizar flujos en un servidor n8n remoto.

## Estructura
```
set up/
├── scripts/
│   ├── daily_briefing.json         # Briefing diario
│   ├── crypto_alerts.json          # Alertas crypto
│   ├── github_backup.json          # Backup automático GitHub
│   ├── uptime_monitor.json         # Monitor de uptime
│   ├── ai_agent_dump.json          # Agente IA
│   ├── fix_*.json / update_*.json  # Versiones corregidas
│   └── ...
├── package.json                    # Solo dependencia: ssh2
└── env_temp.txt                    # Credenciales temporales (¡cuidado!)
```

## Workflows n8n disponibles
| Workflow | Descripción |
|----------|-------------|
| `daily_briefing` | Resumen diario automático |
| `crypto_alerts` | Alertas de precio de crypto |
| `github_auto-backup` | Backup repos a servidor |
| `uptime_monitor` | Monitoreo de servicios |
| `ai_agent` | Agente IA en n8n |

## Notas de seguridad
- `env_temp.txt` contiene credenciales — **NO commitear**
- Los workflows se despliegan via SSH al servidor n8n

## Comandos
```bash
node scripts/update_daily_briefing.json  # Actualizar workflow
```
