#!/bin/bash
# ╔══════════════════════════════════════════════════════════════╗
# ║  Diagnostico y Fix Puerto 80 — Hetzner VPS                  ║
# ║                                                              ║
# ║  Diagnostica que esta usando el puerto 80 y lo libera.       ║
# ║  Compatible con Docker, Nginx, Apache y otros servicios.     ║
# ║                                                              ║
# ║  Uso: bash fix_port80.sh                                     ║
# ║  Ejecutar en el servidor Hetzner como root.                  ║
# ║                                                              ║
# ║  Nota: vida, control tiene su propio fix_port80.sh           ║
# ║  especifico para ULTRA System. Este es el generico.          ║
# ╚══════════════════════════════════════════════════════════════╝

set -euo pipefail

# --- Colores ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  Diagnostico Puerto 80 — Hetzner VPS                    ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# ─── Paso 1: Diagnostico con multiples herramientas ──────
echo -e "${YELLOW}[1/4] Diagnosticando que usa el puerto 80...${NC}"
echo ""

# ss — socket statistics (mas rapido que netstat)
echo -e "${CYAN}--- ss -tlnp (sockets TCP en LISTEN) ---${NC}"
if ss -tlnp | grep -E ":80\b" 2>/dev/null; then
    echo ""
else
    echo -e "  ${GREEN}Nada escuchando en puerto 80 segun ss.${NC}"
    echo ""
fi

# lsof — lista archivos abiertos (incluye sockets)
echo -e "${CYAN}--- lsof -i :80 ---${NC}"
if command -v lsof &>/dev/null; then
    if lsof -i :80 2>/dev/null; then
        echo ""
    else
        echo -e "  ${GREEN}Nada usando puerto 80 segun lsof.${NC}"
        echo ""
    fi
else
    echo -e "  ${YELLOW}lsof no disponible. Instalar con: apt install lsof${NC}"
    echo ""
fi

# Docker — contenedores con puerto 80 mapeado
echo -e "${CYAN}--- docker ps (contenedores con puerto 80) ---${NC}"
if command -v docker &>/dev/null; then
    DOCKER_PORT80=$(docker ps --format "table {{.ID}}\t{{.Names}}\t{{.Ports}}" | grep -E "(:80->|:80/)" 2>/dev/null || true)
    if [ -n "$DOCKER_PORT80" ]; then
        echo "$DOCKER_PORT80"
        echo ""
    else
        echo -e "  ${GREEN}Ningun contenedor Docker mapeado al puerto 80.${NC}"
        echo ""
    fi

    # Tambien listar todos los contenedores para contexto
    echo -e "${CYAN}--- Todos los contenedores Docker ---${NC}"
    docker ps -a --format "table {{.ID}}\t{{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "  Docker no accesible."
    echo ""
else
    echo -e "  ${YELLOW}Docker no instalado.${NC}"
    echo ""
fi

# ─── Paso 2: Identificar y detener servicios conflictivos ─
echo -e "${YELLOW}[2/4] Identificando servicios conflictivos...${NC}"
echo ""

# Buscar servicios comunes que usan puerto 80
CONFLICTS_FOUND=false

# Apache
if systemctl is-active --quiet apache2 2>/dev/null; then
    echo -e "  ${RED}Apache2 esta activo y podria usar puerto 80.${NC}"
    CONFLICTS_FOUND=true
fi

# Nginx (solo conflicto si no es el servicio deseado)
if systemctl is-active --quiet nginx 2>/dev/null; then
    echo -e "  ${CYAN}Nginx esta activo en puerto 80.${NC}"
    # Nginx podria ser el servicio deseado, no marcar como conflicto automaticamente
fi

# Contenedores Docker conflictivos
if command -v docker &>/dev/null; then
    # Obtener nombres de contenedores que usan puerto 80
    CONFLICT_CONTAINERS=$(docker ps --filter "publish=80" --format "{{.Names}}" 2>/dev/null || true)
    if [ -n "$CONFLICT_CONTAINERS" ]; then
        echo -e "  ${RED}Contenedores Docker en puerto 80:${NC}"
        for c in $CONFLICT_CONTAINERS; do
            echo -e "    - $c"
        done
        CONFLICTS_FOUND=true
    fi
fi

if [ "$CONFLICTS_FOUND" = false ]; then
    echo -e "  ${GREEN}No se detectaron conflictos obvios.${NC}"
fi
echo ""

# ─── Paso 3: Liberar puerto 80 ───────────────────────────
echo -e "${YELLOW}[3/4] Liberando puerto 80...${NC}"
echo ""

# Detener contenedores Docker conflictivos
if command -v docker &>/dev/null && [ -n "${CONFLICT_CONTAINERS:-}" ]; then
    echo -e "  ${CYAN}Deteniendo contenedores Docker conflictivos...${NC}"
    for container in $CONFLICT_CONTAINERS; do
        echo -n "    Deteniendo $container... "
        docker stop "$container" 2>/dev/null && echo -e "${GREEN}OK${NC}" || echo -e "${YELLOW}ya detenido${NC}"
    done
    echo ""
fi

# Detener Apache si esta corriendo (casi nunca es el servicio deseado en nuestro setup)
if systemctl is-active --quiet apache2 2>/dev/null; then
    echo -e "  ${CYAN}Deteniendo Apache2...${NC}"
    systemctl stop apache2
    systemctl disable apache2
    echo -e "  ${GREEN}Apache2 detenido y deshabilitado.${NC}"
    echo ""
fi

# ─── Paso 4: Verificar y configurar el servicio deseado ──
echo -e "${YELLOW}[4/4] Verificacion final...${NC}"
echo ""

# Esperar un momento para que los puertos se liberen
sleep 2

# Verificar que el puerto 80 esta libre
if ss -tlnp | grep -qE ":80\b"; then
    echo -e "${CYAN}Estado actual del puerto 80:${NC}"
    ss -tlnp | grep -E ":80\b"
    echo ""
    echo -e "${YELLOW}Puerto 80 sigue ocupado. Puede que sea el servicio deseado (Nginx, Docker Compose).${NC}"
    echo -e "${YELLOW}Si necesitas liberarlo completamente, detener el proceso manualmente.${NC}"
else
    echo -e "${GREEN}Puerto 80 esta libre.${NC}"
    echo ""

    # Sugerir siguiente paso
    echo -e "${CYAN}Siguiente paso: levantar el servicio deseado.${NC}"
    echo ""
    echo "  Opcion A — Docker Compose (ULTRA System):"
    echo "    cd /ruta/proyecto && docker compose up -d"
    echo ""
    echo "  Opcion B — Nginx:"
    echo "    systemctl start nginx"
    echo ""
fi

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  Diagnostico completado                                  ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
