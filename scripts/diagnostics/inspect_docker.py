"""
inspect_docker.py — Inspecciona variables de entorno del contenedor n8n.

Combina funcionalidad de inspect_docker + inspect_docker2.
Muestra todas las variables y resalta las de N8N_.
"""

from shared_config import get_ssh_client


def main():
    ssh = get_ssh_client()

    _, o, _ = ssh.exec_command('docker inspect --format="{{range .Config.Env}}{{println .}}{{end}}" n8n-n8n-1')
    all_env = o.read().decode().strip().split("\n")

    print("=== ALL ENV ===")
    for line in all_env:
        print(line)

    print("\n=== N8N_ ENV (filtered) ===")
    for line in all_env:
        if "N8N_" in line:
            print(line)

    ssh.close()


if __name__ == "__main__":
    main()
