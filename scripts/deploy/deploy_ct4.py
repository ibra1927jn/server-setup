"""Deploy CT4 to Hetzner VPS via SSH/SFTP (password auth)"""

import os

from shared_config import VPS_HOST, get_ssh_client

LOCAL_DIR = r"C:\Users\ibrab\Desktop\Crypto-Trading-Bot4"
REMOTE_DIR = "/root/Crypto-Trading-Bot4"

# Files/dirs to SKIP (not needed on server)
SKIP = {
    ".git",
    "venv",
    "__pycache__",
    "node_modules",
    ".env",
    "logs",
    "db",
    "docs",
    "web",
    "tests",
}


def deploy():
    print(f"Connecting to {VPS_HOST}...")
    ssh = get_ssh_client()
    sftp = ssh.open_sftp()

    # Create remote directory
    try:
        sftp.stat(REMOTE_DIR)
        print(f"Directory {REMOTE_DIR} already exists")
    except FileNotFoundError:
        print(f"Creating {REMOTE_DIR}...")
        sftp.mkdir(REMOTE_DIR)

    # Walk and upload
    uploaded = 0
    skipped = 0
    for root, dirs, files in os.walk(LOCAL_DIR):
        # Skip unwanted directories
        dirs[:] = [d for d in dirs if d not in SKIP]

        rel_path = os.path.relpath(root, LOCAL_DIR)
        remote_path = REMOTE_DIR if rel_path == "." else f"{REMOTE_DIR}/{rel_path.replace(os.sep, '/')}"

        # Create remote dirs
        if rel_path != ".":
            try:
                sftp.stat(remote_path)
            except FileNotFoundError:
                print(f"  mkdir: {remote_path}")
                _mkdir_p(sftp, remote_path)

        for f in files:
            local_file = os.path.join(root, f)
            remote_file = f"{remote_path}/{f}"
            size = os.path.getsize(local_file)
            if size > 10 * 1024 * 1024:  # Skip files > 10MB
                print(f"  SKIP (>10MB): {f}")
                skipped += 1
                continue
            print(f"  >> {remote_file} ({size // 1024}KB)")
            sftp.put(local_file, remote_file)
            uploaded += 1

    print(f"\n=== Upload complete: {uploaded} files, {skipped} skipped ===")

    # Install requirements on server
    print("\nInstalling Python requirements...")
    commands = [
        f"cd {REMOTE_DIR} && pip3 install -r requirements.txt 2>&1 | tail -5",
        f"ls -la {REMOTE_DIR}/ | head -20",
        f"ls -la {REMOTE_DIR}/*.csv 2>/dev/null | head -5 || echo 'No CSVs yet (normal for fresh deploy)'",
    ]
    for cmd in commands:
        print(f"\n$ {cmd}")
        _, stdout, _stderr = ssh.exec_command(cmd)
        print(stdout.read().decode())

    sftp.close()
    ssh.close()
    print("Done!")


def _mkdir_p(sftp, remote_dir):
    """Recursively create remote directories"""
    parts = remote_dir.split("/")
    current = ""
    for part in parts:
        if not part:
            current = "/"
            continue
        current = f"{current}/{part}" if current != "/" else f"/{part}"
        try:
            sftp.stat(current)
        except FileNotFoundError:
            sftp.mkdir(current)


if __name__ == "__main__":
    deploy()
