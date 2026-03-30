from pathlib import Path

from shared_config import get_ssh_client

_SCRIPTS_DIR = Path(__file__).resolve().parent
_LOG_FILE = _SCRIPTS_DIR / "n8n_full_logs.txt"


def main():
    ssh = get_ssh_client()

    print("Fetching docker logs and saving to local file...")
    _, stdout, stderr = ssh.exec_command("docker logs n8n-n8n-1 --tail 500")
    logs = stdout.read().decode()
    errs = stderr.read().decode()

    with open(_LOG_FILE, "w", encoding="utf-8") as f:
        f.write("=== STDOUT ===\n")
        f.write(logs)
        f.write("\n=== STDERR ===\n")
        f.write(errs)

    print(f"Logs saved to {_LOG_FILE}")
    ssh.close()


if __name__ == "__main__":
    main()
