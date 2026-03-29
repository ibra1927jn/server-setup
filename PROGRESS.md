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
- [2026-03-29] | Heartbeat #8: 3 unused imports removed (test files), 43 new tests (credential extraction, workflow structures, node filtering, connection management, line parsing, template injection). 235/235 passing, 49% coverage (was 43%)
- [2026-03-29] | Heartbeat #7: late imports moved to top of file in 3 telegram bot scripts, 32 new tests (workflow JSON manipulation, node filtering, version patching, import preparation, fase2 data structures). 190/190 passing, coverage improved (was 38%)
- [2026-03-29] | Heartbeat #6: hardcoded password removed from deploy_n8n_hetzner.py (moved to .env via shared_config), 2 unused imports removed (test files), 15 new tests (8 deploy_n8n main/templates + 7 deploy_ct4 deploy function). 154/154 passing, 38% coverage (was 26%)
- [2026-03-29] | Heartbeat #5: duplicate time import removed (fix_chat_payload.py), 15 new tests for deploy helpers (run, _mkdir_p). 129/129 passing, 21% coverage (was 15%)
- [2026-03-29] | Heartbeat #4: missing time import fix (query_n8n_db.py), 12 unnecessary f-string prefixes removed across 8 files, 103 new tests (5 check_server + 98 syntax validation). 114/114 passing, 15% coverage (was 11%)
- [2026-03-29] | Heartbeat #3: 10 bare except→Exception across 9 files, unused MagicMock import removed, 6 new SSH auth tests (11/11 passing, shared_config 97% coverage)
- [2026-03-29] | Heartbeat #2: 9 more unused imports removed, 3 bare except→Exception, hardcoded chat ID→env, 5 pytest unit tests for shared_config (5/5 passing)
- [2026-03-29] | Heartbeat: pytest config (pyproject.toml + conftest.py), test collection fixed (13 errors → 0), hardcoded creds removed from fix_n8n_login.py, 9 unused imports cleaned
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
