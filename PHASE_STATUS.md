# Heartbeat — Phase Status

## Phase 1.0: Server Health
**Status:** ✅ COMPLETADA
**Componente:** `health.sh`
**Descripción:** Monitoreo de salud del servidor (disco, RAM, CPU, servicios).

## Phase 1.1: Priority Engine
**Status:** ✅ COMPLETADA
**Componente:** `priority-engine.sh`
**Descripción:** Motor de prioridades que calcula scores por proyecto según actividad, tests fallidos, tiempo sin check, etc.

## Phase 1.2: Safety Layer
**Status:** ✅ COMPLETADA
**Componentes:** `circuit-breaker.sh`, `auto-rollback.sh`
**Descripción:** Circuit breaker (bloquea proyectos con fallos repetidos) + auto-rollback (revierte si tests fallan post-commit).

## Phase 1.3: Agent Teams en Paralelo
**Status:** ✅ COMPLETADA
**Fecha completada:** 2026-03-30
**Componentes:** `agent-launcher.sh`, `team-coordinator.sh`
**Descripción:** Sistema de agentes autónomos en paralelo via tmux.

### Validación:
- `agent-launcher.sh`: Lanza sesiones tmux, rechaza duplicados, respeta circuit breaker, valida repos
- `team-coordinator.sh`: Calcula max agentes por RAM/CPU (0-3), timeout 60min, limpieza de sesiones muertas
- `heartbeat.sh`: Integración en Phase 4 — llama `coordinate_agents` + incluye reporte en Telegram
- CLI: `team-coordinator.sh {status|report|run|cleanup}` funcional
- Dependencias: `circuit-breaker.sh`, `priority-engine.sh` resuelven correctamente
- Logs: `logs/agents.jsonl`, `logs/team-coordinator.log`, `agent-state.json`
