# RESUMEN: vida, control (Infrastructure / Deploy Hetzner)

**Stack:** Node.js (ssh2, ssh2-sftp-client), Docker Compose
**Última modificación:** Mar 24, 2026

## Descripción
Infraestructura y scripts de despliegue para el servidor Hetzner. Contiene el "ultra-engine" y scripts de deploy/gestión remota.

## Estructura
```
vida, control/
├── ultra-engine/           # Motor principal desplegado
├── scripts/                # Scripts de gestión
├── db/                     # Datos/esquemas de BD
├── deploy_hetzner.js       # Script de deploy SSH (3k)
├── docker-compose.yml      # Stack Docker completo (3k)
├── deploy.tar.gz           # Build empaquetado (28MB)
├── .env.example            # Variables requeridas
└── docs/
    ├── ARCHITECTURE.md     # Arquitectura del sistema
    └── ULTRA_SYSTEM_AUDIT.md
```

## Variables de entorno
- `.env.example` → copiar a `.env`
- Necesita: host Hetzner, usuario SSH, contraseñas DB

## Comandos
```bash
node deploy_hetzner.js      # Deploy al servidor
docker-compose up -d        # Levantar stack local
```

## Relación con otros proyectos
- Despliega los servicios que usan `Crypto-Trading-Bot4`
- Posiblemente aloja el servidor n8n de `set up`
- `deploy.tar.gz` = build empaquetado listo para subir

## Docs
- `docs/ARCHITECTURE.md` — arquitectura completa
- `docs/ULTRA_SYSTEM_AUDIT.md` — auditoría del sistema
- `project_audit_valuation.md` — valoración del proyecto
