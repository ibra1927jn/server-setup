#!/bin/bash
# ╔══════════════════════════════════════════════════════════════╗
# ║  Migracion de SSH Keys — Hetzner VPS                        ║
# ║                                                              ║
# ║  Este script automatiza la migracion de autenticacion por    ║
# ║  password a SSH keys en un servidor Hetzner.                 ║
# ║                                                              ║
# ║  Uso: bash migrate_ssh_keys.sh <SERVER_IP>                   ║
# ║  Ejecutar desde la maquina LOCAL (no el servidor).           ║
# ║                                                              ║
# ║  IMPORTANTE: El script mantiene una sesion SSH de seguridad  ║
# ║  abierta durante la migracion para evitar quedarse fuera.    ║
# ╠══════════════════════════════════════════════════════════════╣
# ║  ROLLBACK (si algo sale mal):                                ║
# ║                                                              ║
# ║  1. Usar la sesion SSH de seguridad que queda abierta        ║
# ║  2. Restaurar la config original:                            ║
# ║     cp /etc/ssh/sshd_config.bak.YYYYMMDD /etc/ssh/sshd_config║
# ║  3. Reiniciar sshd:                                         ║
# ║     systemctl restart sshd                                   ║
# ║  4. Verificar que puedes conectarte con password             ║
# ║                                                              ║
# ║  Si perdiste acceso total:                                   ║
# ║  - Usar la consola de Hetzner Cloud (rescue mode)            ║
# ║  - Montar el disco y restaurar sshd_config.bak.*             ║
# ╚══════════════════════════════════════════════════════════════╝

set -euo pipefail

# --- Colores ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# --- Validar argumentos ---
if [ $# -lt 1 ]; then
    echo -e "${RED}Error: Se requiere la IP del servidor.${NC}"
    echo "Uso: bash migrate_ssh_keys.sh <SERVER_IP> [SSH_USER]"
    echo "Ejemplo: bash migrate_ssh_keys.sh 95.217.158.7 root"
    exit 1
fi

SERVER_IP="$1"
SSH_USER="${2:-root}"
SSH_KEY_PATH="$HOME/.ssh/id_ed25519"
SSH_PORT=22
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  SSH Key Migration — Hetzner VPS                        ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo -e "  Servidor:  ${CYAN}${SSH_USER}@${SERVER_IP}${NC}"
echo -e "  Key path:  ${CYAN}${SSH_KEY_PATH}${NC}"
echo -e "  Timestamp: ${CYAN}${TIMESTAMP}${NC}"
echo ""

# ─── Paso 1: Generar SSH key si no existe ─────────────────
echo -e "${YELLOW}[1/6] Verificando SSH key local...${NC}"

if [ -f "$SSH_KEY_PATH" ]; then
    echo -e "  ${GREEN}Key ed25519 ya existe: ${SSH_KEY_PATH}${NC}"
else
    echo -e "  ${CYAN}Generando nueva key ed25519...${NC}"
    # Crear directorio .ssh si no existe
    mkdir -p "$HOME/.ssh"
    chmod 700 "$HOME/.ssh"
    # Generar key sin passphrase (Allan puede agregar una despues)
    ssh-keygen -t ed25519 -C "allan@hetzner-vps-${TIMESTAMP}" -f "$SSH_KEY_PATH" -N ""
    echo -e "  ${GREEN}Key generada exitosamente.${NC}"
fi

echo -e "  Fingerprint: $(ssh-keygen -lf "$SSH_KEY_PATH" 2>/dev/null || echo 'no disponible')"
echo ""

# ─── Paso 2: Copiar public key al servidor ────────────────
echo -e "${YELLOW}[2/6] Copiando public key al servidor...${NC}"
echo -e "  ${CYAN}Se pedira la password del servidor (ultima vez).${NC}"
echo ""

# Usar ssh-copy-id para copiar la key
if ssh-copy-id -i "${SSH_KEY_PATH}.pub" -p "$SSH_PORT" "${SSH_USER}@${SERVER_IP}"; then
    echo -e "  ${GREEN}Public key copiada exitosamente.${NC}"
else
    echo -e "  ${RED}Error al copiar la key. Verificar que el servidor acepta password auth.${NC}"
    exit 1
fi
echo ""

# ─── Paso 3: Verificar conexion con key ───────────────────
echo -e "${YELLOW}[3/6] Verificando conexion SSH con key (sin password)...${NC}"

if ssh -i "$SSH_KEY_PATH" -o PasswordAuthentication=no -o BatchMode=yes -p "$SSH_PORT" "${SSH_USER}@${SERVER_IP}" "echo 'SSH_KEY_AUTH_OK'" 2>/dev/null | grep -q "SSH_KEY_AUTH_OK"; then
    echo -e "  ${GREEN}Conexion con key funciona correctamente.${NC}"
else
    echo -e "  ${RED}Error: No se pudo autenticar con la key.${NC}"
    echo -e "  ${RED}Abortando. No se modificara sshd_config.${NC}"
    exit 1
fi
echo ""

# ─── Paso 4: Abrir sesion SSH de seguridad ────────────────
echo -e "${YELLOW}[4/6] Abriendo sesion SSH de seguridad en background...${NC}"
echo -e "  ${CYAN}Esta sesion quedara abierta como respaldo durante la migracion.${NC}"

# Abrir sesion de seguridad que mantiene conexion viva
# Si algo sale mal, esta sesion permite revertir
ssh -i "$SSH_KEY_PATH" -o ServerAliveInterval=30 -o ServerAliveCountMax=10 \
    -p "$SSH_PORT" "${SSH_USER}@${SERVER_IP}" \
    "echo 'Sesion de seguridad activa. PID: $$'; sleep 3600" &
SAFETY_SSH_PID=$!

# Dar tiempo para que la conexion se establezca
sleep 2

if kill -0 "$SAFETY_SSH_PID" 2>/dev/null; then
    echo -e "  ${GREEN}Sesion de seguridad activa (PID: ${SAFETY_SSH_PID}).${NC}"
else
    echo -e "  ${RED}Error: No se pudo abrir sesion de seguridad. Abortando.${NC}"
    exit 1
fi
echo ""

# ─── Paso 5: Backup y modificar sshd_config ──────────────
echo -e "${YELLOW}[5/6] Configurando sshd en el servidor...${NC}"

# Script remoto que se ejecuta en el servidor
ssh -i "$SSH_KEY_PATH" -p "$SSH_PORT" "${SSH_USER}@${SERVER_IP}" bash -s "$TIMESTAMP" << 'REMOTE_SCRIPT'
    set -euo pipefail
    TIMESTAMP="$1"

    echo "  [remoto] Creando backup de sshd_config..."
    cp /etc/ssh/sshd_config "/etc/ssh/sshd_config.bak.${TIMESTAMP}"
    echo "  [remoto] Backup guardado: /etc/ssh/sshd_config.bak.${TIMESTAMP}"

    echo "  [remoto] Modificando sshd_config..."

    # Deshabilitar autenticacion por password
    # Usar sed para modificar o agregar las directivas
    SSHD_CONFIG="/etc/ssh/sshd_config"

    # PasswordAuthentication no
    if grep -qE "^#?PasswordAuthentication" "$SSHD_CONFIG"; then
        sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication no/' "$SSHD_CONFIG"
    else
        echo "PasswordAuthentication no" >> "$SSHD_CONFIG"
    fi

    # ChallengeResponseAuthentication no
    if grep -qE "^#?ChallengeResponseAuthentication" "$SSHD_CONFIG"; then
        sed -i 's/^#\?ChallengeResponseAuthentication.*/ChallengeResponseAuthentication no/' "$SSHD_CONFIG"
    else
        echo "ChallengeResponseAuthentication no" >> "$SSHD_CONFIG"
    fi

    # KbdInteractiveAuthentication no (nombre nuevo en OpenSSH 8.7+)
    if grep -qE "^#?KbdInteractiveAuthentication" "$SSHD_CONFIG"; then
        sed -i 's/^#\?KbdInteractiveAuthentication.*/KbdInteractiveAuthentication no/' "$SSHD_CONFIG"
    else
        echo "KbdInteractiveAuthentication no" >> "$SSHD_CONFIG"
    fi

    # Asegurar que PubkeyAuthentication esta habilitado
    if grep -qE "^#?PubkeyAuthentication" "$SSHD_CONFIG"; then
        sed -i 's/^#\?PubkeyAuthentication.*/PubkeyAuthentication yes/' "$SSHD_CONFIG"
    else
        echo "PubkeyAuthentication yes" >> "$SSHD_CONFIG"
    fi

    # Verificar la config antes de reiniciar
    echo "  [remoto] Verificando sshd_config..."
    if sshd -t; then
        echo "  [remoto] Config valida. Reiniciando sshd..."
        systemctl restart sshd
        echo "  [remoto] sshd reiniciado."
    else
        echo "  [remoto] ERROR: Config invalida. Restaurando backup..."
        cp "/etc/ssh/sshd_config.bak.${TIMESTAMP}" /etc/ssh/sshd_config
        echo "  [remoto] Backup restaurado. sshd NO fue modificado."
        exit 1
    fi

    # Mostrar config actual para verificacion
    echo ""
    echo "  [remoto] Configuracion actual:"
    echo "  PasswordAuthentication: $(grep -E '^PasswordAuthentication' /etc/ssh/sshd_config || echo 'no encontrado')"
    echo "  ChallengeResponseAuth:  $(grep -E '^ChallengeResponseAuthentication' /etc/ssh/sshd_config || echo 'no encontrado')"
    echo "  PubkeyAuthentication:   $(grep -E '^PubkeyAuthentication' /etc/ssh/sshd_config || echo 'no encontrado')"
REMOTE_SCRIPT

echo ""

# ─── Paso 6: Verificacion final ──────────────────────────
echo -e "${YELLOW}[6/6] Verificacion final...${NC}"

# Verificar que la conexion con key sigue funcionando despues del cambio
if ssh -i "$SSH_KEY_PATH" -o PasswordAuthentication=no -o BatchMode=yes -p "$SSH_PORT" "${SSH_USER}@${SERVER_IP}" "echo 'POST_MIGRATION_OK'" 2>/dev/null | grep -q "POST_MIGRATION_OK"; then
    echo -e "  ${GREEN}Conexion con key funciona post-migracion.${NC}"
else
    echo -e "  ${RED}ERROR: No se pudo conectar despues de la migracion.${NC}"
    echo -e "  ${RED}Usa la sesion de seguridad para revertir:${NC}"
    echo -e "  ${RED}  cp /etc/ssh/sshd_config.bak.${TIMESTAMP} /etc/ssh/sshd_config${NC}"
    echo -e "  ${RED}  systemctl restart sshd${NC}"
    exit 1
fi

# Verificar que password auth esta deshabilitado
if ssh -i "$SSH_KEY_PATH" -p "$SSH_PORT" "${SSH_USER}@${SERVER_IP}" \
    "sshd -T 2>/dev/null | grep -i passwordauthentication" 2>/dev/null | grep -qi "no"; then
    echo -e "  ${GREEN}Password authentication deshabilitado correctamente.${NC}"
else
    echo -e "  ${YELLOW}Advertencia: No se pudo confirmar que password auth esta deshabilitado.${NC}"
    echo -e "  ${YELLOW}Verificar manualmente: ssh ${SSH_USER}@${SERVER_IP} 'sshd -T | grep password'${NC}"
fi

# Limpiar sesion de seguridad
kill "$SAFETY_SSH_PID" 2>/dev/null || true

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  Migracion completada exitosamente                      ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo -e "  ${GREEN}Key:      ${SSH_KEY_PATH}${NC}"
echo -e "  ${GREEN}Servidor: ${SSH_USER}@${SERVER_IP}${NC}"
echo -e "  ${GREEN}Backup:   /etc/ssh/sshd_config.bak.${TIMESTAMP}${NC}"
echo ""
echo -e "  ${CYAN}Para conectarte:${NC}"
echo -e "  ssh -i ${SSH_KEY_PATH} ${SSH_USER}@${SERVER_IP}"
echo ""
echo -e "  ${YELLOW}ROLLBACK si hay problemas:${NC}"
echo -e "  1. Conectar via Hetzner Cloud Console (rescue mode)"
echo -e "  2. cp /etc/ssh/sshd_config.bak.${TIMESTAMP} /etc/ssh/sshd_config"
echo -e "  3. systemctl restart sshd"
echo ""
