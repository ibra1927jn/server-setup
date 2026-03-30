import time

from shared_config import get_ssh_client


def main():
    ssh = get_ssh_client()

    # Find where bcryptjs is in the container
    find_cmd = (
        "docker exec n8n-n8n-1 find /usr/local/lib/node_modules/n8n"
        " -name 'bcryptjs' -type d 2>/dev/null | head -3"
    )
    _, o, _ = ssh.exec_command(find_cmd)
    time.sleep(3)
    bcrypt_paths = o.read().decode().strip()
    print("=== BCRYPTJS PATHS ===")
    print(bcrypt_paths)

    # Also find better-sqlite3
    find_cmd2 = (
        "docker exec n8n-n8n-1 find /usr/local/lib/node_modules/n8n"
        " -name 'better-sqlite3' -type d 2>/dev/null | head -3"
    )
    _, o2, _ = ssh.exec_command(find_cmd2)
    time.sleep(3)
    sqlite_paths = o2.read().decode().strip()
    print("\n=== BETTER-SQLITE3 PATHS ===")
    print(sqlite_paths)

    ssh.close()


if __name__ == "__main__":
    main()
