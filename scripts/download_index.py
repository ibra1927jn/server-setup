from shared_config import get_ssh_client


def main():
    ssh = get_ssh_client()

    sftp = ssh.open_sftp()
    local_path = "/tmp/dashboard_index.html"
    sftp.get("/var/www/dashboard/index.html", local_path)
    sftp.close()
    ssh.close()


if __name__ == "__main__":
    main()
