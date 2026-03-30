from shared_config import get_ssh_client


def main():
    ssh = get_ssh_client()

    print("Fetching docker logs and saving to local file...")
    stdin, stdout, stderr = ssh.exec_command('docker logs n8n-n8n-1 --tail 500')
    logs = stdout.read().decode()
    errs = stderr.read().decode()

    with open(r"C:\Users\ibrab\Desktop\set up\scripts\n8n_full_logs.txt", "w", encoding="utf-8") as f:
        f.write("=== STDOUT ===\n")
        f.write(logs)
        f.write("\n=== STDERR ===\n")
        f.write(errs)

    print("Logs saved to C:\\Users\\ibrab\\Desktop\\set up\\scripts\\n8n_full_logs.txt")
    ssh.close()


if __name__ == "__main__":
    main()
