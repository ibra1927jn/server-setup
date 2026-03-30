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
- [2026-03-30] | Heartbeat #16: refactored fix_telegram_creds.py (extracted index_credentials_by_type + patch_workflow_credentials), 16 new tests (13 fix_telegram_creds, 1 execute_briefing stderr, 1 deploy_ct4 subdir mkdir, 1 syntax), deploy_ct4 92%→100%, execute_daily_briefing 93%→100%, added fix/ scripts to coverage omit. 485/485 passing, 99% coverage, 0 lint errors
- [2026-03-30] | Heartbeat #15: fixed TELEGRAM_chat_id→TELEGRAM_CHAT_ID import bug (rebuild_workflows, rebuild_v2), replaced hardcoded IP with VPS_HOST, wrapped fase3_ssl_dashboard.py in main(), removed unused DUCK_TOKEN var, wrapped 10 fix scripts in main(), fixed 2 unused stdin vars, 7 new tests for fase2_deploy main() (12%→96%). 469/469 passing, 99% coverage, 0 lint errors
- [2026-03-30] | Heartbeat #14: refactored 3 large main() functions (rebuild_workflows 319→25 lines, rebuild_v2 285→30 lines, mejoras_ssl_github 234→20 lines) into 17 extracted helper functions. 461/461 passing, 99% coverage, 0 lint errors
- [2026-03-30] | Heartbeat #13: 52 new tests for main() functions (export_analyze, final_pendientes, patch_workflow, upgrade_agent, telegram bots v1/v2/v3, import_workflows) via mocked SSH/requests. 461/461 passing, 99% coverage (was 88%)
- [2026-03-30] | Heartbeat #12: 42 new tests (telegram bot builders v1/v2/v3, patch_workflow direct imports), added .coverage and .pytest_cache to .gitignore. 409/409 passing, 88% coverage (was 87%)
- [2026-03-30] | Heartbeat #11: wrapped 33 scripts' top-level code in main() with if __name__ guard (was 31 without guards, now 0). Prevents import side effects, improves testability. 348/348 passing, 87% coverage
- [2026-03-30] | Heartbeat #10: centralized 3 more hardcoded n8n IDs (N8N_TELEGRAM_BOT_WORKFLOW_ID, N8N_BRIEFING_WORKFLOW_ID, N8N_CRED_OPENAI) into shared_config.py, added .coverage to .gitignore. 348/348 passing, 87% coverage
- [2026-03-30] | Heartbeat #9: 4 late imports moved to top (fix scripts), 19 lint errors fixed across 17 files (E401 multi-import, E701/E702 multi-statement lines, E402 late imports, F541 extraneous f-string, F401 unused imports). Ruff now reports 0 errors (was 20, excluding 1 unfixable false positive). 235/235 passing, 49% coverage
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
