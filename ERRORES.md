# ERRORES.md — Lo que no volvemos a hacer

## Formato
[Fecha] | [Archivo afectado] | [Error] | [Fix aplicado]

---

## TypeScript
- [2026-03-27] | global | Usar ny en tipos → errores en runtime silenciosos
  FIX: tipar siempre explícitamente, especialmente payloads de DB

## Seguridad
- [2026-03-28] | .gitignore | Archivo corrupto (caracteres separados por espacios: `. e n v`) | Reescrito con entradas correctas: .env, node_modules/, __pycache__/, *.pyc, *.log, n8n_env.txt, n8n_full_logs.txt, exported_workflows.json
- [2026-03-28] | 8 scripts (check_exec_error, export_analyze_workflow, fix_telegram_cred, patch_workflow, reset_password_direct, reset_pw_v2, reset_pw_v3, verify_login) | Credenciales n8n hardcodeadas (email + password Admin2026!) | Reemplazado por imports de shared_config (N8N_EMAIL, N8N_PASSWORD)
- [2026-03-28] | scripts/exported_workflows.json | Archivo vacio de 0 bytes en el repo | Eliminado y agregado a .gitignore
- [2026-03-28] | scripts/.env | PENDIENTE VERIFICAR: ejecutar `git log --all --oneline -- scripts/.env` para confirmar si credenciales fueron commiteadas al historial. Si es asi, considerar BFG Repo-Cleaner o git filter-branch | Allan debe verificar manualmente

## General
- [TEMPLATE] | cualquier módulo | Marcar tarea como done sin tests
  FIX: tests en verde antes de actualizar PROGRESS.md
