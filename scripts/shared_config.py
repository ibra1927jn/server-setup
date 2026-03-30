"""
shared_config.py — Configuracion centralizada de credenciales.

Carga variables desde .env usando python-dotenv.
Si .env no existe, usa variables de entorno del sistema como fallback.
Provee get_ssh_client() para conexion SSH reutilizable via paramiko.
"""

import os
from pathlib import Path

import paramiko
from dotenv import load_dotenv

# Cargar .env desde el mismo directorio que este archivo
_env_path = Path(__file__).parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path)

# --- Hetzner VPS ---
VPS_HOST: str = os.getenv("VPS_HOST", "")
VPS_USER: str = os.getenv("VPS_USER", "root")
VPS_PASS: str = os.getenv("VPS_PASS", "")
VPS_SSH_KEY_PATH: str = os.getenv("VPS_SSH_KEY_PATH", "")

# --- n8n ---
N8N_URL: str = os.getenv("N8N_URL", f"http://{VPS_HOST}:5678")
N8N_EMAIL: str = os.getenv("N8N_EMAIL", "")
N8N_PASSWORD: str = os.getenv("N8N_PASSWORD", "")
N8N_API_KEY: str = os.getenv("N8N_API_KEY", "")

# --- Telegram ---
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")

# --- OpenRouter ---
OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")

# --- GitHub ---
GITHUB_PAT: str = os.getenv("GITHUB_PAT", "")

# --- n8n Workflow IDs ---
N8N_AI_WORKFLOW_ID: str = os.getenv("N8N_AI_WORKFLOW_ID", "WiTcSI66bHwdSgkd")

# --- Headers reutilizables para n8n API ---
N8N_HEADERS: dict = {
    "X-N8N-API-KEY": N8N_API_KEY,
    "Content-Type": "application/json",
}


def get_ssh_client(
    host: str = "",
    user: str = "",
    password: str = "",
    key_path: str = "",
    timeout: int = 10,
) -> paramiko.SSHClient:
    """
    Retorna un paramiko.SSHClient conectado al VPS.

    Usa los parametros pasados o las constantes del modulo como fallback.
    Prioridad: key_path > password > agente SSH del sistema.
    """
    host = host or VPS_HOST
    user = user or VPS_USER
    password = password or VPS_PASS
    key_path = key_path or VPS_SSH_KEY_PATH

    if not host:
        raise ValueError("VPS_HOST no configurado. Revisa .env o variables de entorno.")

    client = paramiko.SSHClient()
    # Aceptar hosts desconocidos automaticamente (entorno controlado)
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    if key_path and Path(key_path).exists():
        # Autenticacion por llave SSH
        client.connect(hostname=host, username=user, key_filename=key_path, timeout=timeout)
    elif password:
        # Autenticacion por password
        client.connect(hostname=host, username=user, password=password, look_for_keys=False, timeout=timeout)
    else:
        # Fallback: usa agente SSH del sistema operativo
        client.connect(hostname=host, username=user, allow_agent=True, look_for_keys=True, timeout=timeout)

    return client
