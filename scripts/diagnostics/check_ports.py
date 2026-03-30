"""
check_ports.py — Verifica puertos abiertos y errores de nginx en el VPS.

Combina la funcionalidad de check_ports + check_ports2.
"""

from shared_config import get_ssh_client


def main():
    ssh = get_ssh_client()

    print("=== PORT BINDINGS ===")
    _, o, _ = ssh.exec_command('ss -tlnp | grep -E "(80|443|5678)"')
    lines = o.read().decode().strip().split("\n")
    for line in lines:
        print(line)

    print("\n=== NGINX ERRORS ===")
    _, o, _ = ssh.exec_command("tail -n 10 /var/log/nginx/error.log")
    print(o.read().decode())

    ssh.close()


if __name__ == "__main__":
    main()
