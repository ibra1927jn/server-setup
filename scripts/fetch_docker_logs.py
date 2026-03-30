from shared_config import get_ssh_client


def main():
    ssh = get_ssh_client()

    print("Fetching docker logs...")
    _, stdout, stderr = ssh.exec_command("docker logs n8n-n8n-1 --tail 100")
    logs = stdout.read().decode()
    errs = stderr.read().decode()

    print("STDOUT:", logs[-2000:])
    print("STDERR:", errs[-2000:])

    ssh.close()


if __name__ == "__main__":
    main()
