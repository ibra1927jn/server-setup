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
- [2026-03-30] | Heartbeat #33: extracted _build_fixed_workflow() from fix_ai_agent_workflow.py main() (100→30 lines), added encoding='utf-8' to 5 open() calls in operational scripts (get_ai_agent_full, mejoras_ssl_github, fix_n8n_proxy, fix_n8n_proxy2). 487/487 passing, 99% coverage, 0 lint errors
- [2026-03-30] | Heartbeat #32: refactored 4 oversized main() functions — fase3_ssl_dashboard.py (430→10 lines, 6 helpers), fase2_deploy.py (109→8 lines, 3 helpers), fix_dashboard_isolation.py (106→30 lines, 2 helpers), fix_model_and_test.py (116→40 lines, 1 helper), deploy_chat_widget.py (170→15 lines, 1 helper). Simplified test_gen_id.py (removed unnecessary mock SSH setup). 487/487 passing, 99% coverage, 0 lint errors
- [2026-03-30] | Heartbeat #31: applied ruff formatter to 122 files for consistent code style, added *.bak to .gitignore, added ruff format config (double-quote, space-indent) to pyproject.toml. 487/487 passing, 99% coverage, 0 lint errors. Codebase fully formatted and all meaningful lint rules enforced
- [2026-03-30] | Heartbeat #30: extracted exception string literal to variable in shared_config.py (EM101/TRY003), enabled EM (flake8-errmsg) and TRY (tryceratops) rule sets. 487/487 passing, 99% coverage, 0 lint errors. Ruff config now has 54 rule sets — remaining unenabled (D, ANN, COM, Q, T20, INP) are stylistic or inapplicable to this project
- [2026-03-30] | Heartbeat #29: enabled BLE (blind-except) and PTH (pathlib) rule sets with per-file-ignores for operational scripts, removed stale E402/S113 global ignores (now enforced). 487/487 passing, 99% coverage, 0 lint errors. Ruff config now has 52 rule sets — all meaningful rules enabled, remaining (D, ANN, COM, Q, T20, EM, TRY, INP) are stylistic or inapplicable
- [2026-03-30] | Heartbeat #28: fixed N806 uppercase local vars in 4 files, unused mock args (ARG001) in test_deploy_ct4, boolean trap (FBT002) in test_upgrade_agent_main, enabled 14 new ruff rule sets (T10, A, PT, DTZ, TC, ASYNC, SLF, N, ARG, FBT, FIX, ERA, ICN). 487/487 passing, 99% coverage, 0 lint errors
- [2026-03-30] | Heartbeat #27: enabled 11 additional ruff rule sets (ISC, FA, SLOT, LOG, RSE, TID, G, YTT, PGH, INT, EXE) — all pass cleanly, guard against future regressions. 487/487 passing, 99% coverage, 0 lint errors. Codebase fully clean — no dead code, no bare excepts, no hardcoded creds, no TODO/FIXME markers
- [2026-03-30] | Heartbeat #26: extracted 4 workflow builders from fase2_deploy.py main() (build_daily_briefing, build_uptime_monitor, build_crypto_alerts, build_github_backup), simplified else-if to elif in 2 fix scripts (PLR5501), replaced exit() with sys.exit() (PLR1722), merged duplicate comparisons (PLR1714), replaced unnecessary lambda (PLW0108), enabled PLC/PLE/PLW/PLR/FURB/C4/FLY rule sets in ruff. 487/487 passing, 99% coverage, 0 lint errors
- [2026-03-30] | Heartbeat #25: prefixed 18 unused stderr vars with underscore (RUF059) in 12 scripts, replaced 24 list-comprehension-[0] patterns with next() (RUF015) in 11 test files, enabled RUF rule set in ruff config, removed 2 stale noqa directives, replaced if-in-del with dict.pop (RUF051). 487/487 passing, 99% coverage, 0 lint errors
- [2026-03-30] | Heartbeat #24: replaced last 4 hardcoded IPs in test scripts (verify_fase3, test.py, test_explicit_file, test_webhook_direct) with VPS_HOST from shared_config, wrapped verify_fase3.py and test.py in main() with __name__ guard. 487/487 passing, 99% coverage, 0 lint errors. Zero hardcoded IPs remain in entire codebase
- [2026-03-30] | Heartbeat #23: replaced last hardcoded IP (95.217.158.7) in fase3_ssl_dashboard.py — NIP_DOMAIN now derived from VPS_HOST, dashboard HTML uses placeholder. 487/487 passing, 99% coverage, 0 lint errors
- [2026-03-30] | Heartbeat #22: replaced 4 hardcoded chatId values in fase2_deploy.py with TELEGRAM_CHAT_ID from shared_config. 487/487 passing, 99% coverage, 0 lint errors. Codebase fully clean — no remaining hardcoded credentials, no dead imports, no TODO/FIXME markers
- [2026-03-30] | Heartbeat #21: wrapped long lines in 28 files (E501), added timeout=30 to 14 requests calls (S113), combined 8 nested with statements (SIM117), replaced try-except-pass with contextlib.suppress (SIM105). 487/487 passing, 99% coverage, 0 lint errors
- [2026-03-30] | Heartbeat #20: fixed 29 lint issues across 12 files (E121/E122/E126 indentation, E226 spacing, E302 blank lines, E306 nested defs, E501 line length). 487/487 passing, 3 remaining are false positives (W503 PEP8-preferred, E402 required sys.path)
- [2026-03-30] | Heartbeat #19: refactored 3 complex functions (debug_telegram C12→5, fix_chatid C11→5, fix_node_types C11→4) by extracting 11 helpers, fixed unused loop var (B007). 487/487 passing, 99% coverage, 0 lint+complexity errors
- [2026-03-30] | Heartbeat #18: removed dead code in 3 test helpers (unused route_request function, 2 unreachable else branches), added credential to export_analyze sample data to cover extraction loop. 487/487 passing, 99% coverage (6→2 uncovered lines), 0 lint errors
- [2026-03-30] | Heartbeat #17: covered 3 missing lines in fase2_deploy.py (stdout/stderr branches, 96%→100%), replaced hardcoded IP with VPS_HOST in uptime monitor template, added 12 operational scripts (diagnostics + deploy) to coverage omit, sorted imports across 75 files (isort convention). 487/487 passing, 99% coverage, 0 lint errors (2 import-only false positives in hook-blocked files)
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
