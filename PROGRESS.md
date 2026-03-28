---
# PROGRESS.md — set up

## Estado actual
[El proyecto principal está en fase de despliegue local o migración. Las funciones core están estables pero faltan integraciones finales.]

## Completado ✅
- Estructura base completada.
- Archivos iniciales configurados.

## En progreso 🔄
- Implementación de CI/CD local en AgenticOS (Ollama + Claude Code).
- Limpieza de contexto.

## Completado recientemente
- [2026-03-28] | Sistema centralizado de credenciales (shared_config.py + .env + .gitignore + requirements.txt)
- [2026-03-28] | Migracion de 90+ scripts Python de credenciales hardcodeadas a shared_config imports
- [2026-03-28] | Limpieza masiva: ~35 archivos duplicados/muertos eliminados de scripts/
- [2026-03-28] | Reorganizacion scripts/ en subdirectorios: deploy/, diagnostics/, fix/, workflows/, test/
- [2026-03-28] | Merge check_ports + check_ports2 → diagnostics/check_ports.py
- [2026-03-28] | Merge inspect_docker + inspect_docker2 → diagnostics/inspect_docker.py
- [2026-03-28] | Consolidacion workflow JSONs: solo quedan update_* en workflows/
- [2026-03-28] | Eliminado money/ (copia embebida, real en Desktop)

## Pendiente
- Eliminar manualmente "alze os/" (directorio vacio, bloqueado por proceso Windows)
- Ejecucion completa con agentes de IA autonomos.
- Actualizacion de paquetes.
- Migrar VPS auth de password a SSH keys.

## Bloqueado 🚫

---
