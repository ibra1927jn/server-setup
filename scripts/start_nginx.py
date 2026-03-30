import time

from shared_config import get_ssh_client


def main():
    ssh = get_ssh_client()

    ssh.exec_command("systemctl start nginx")
    time.sleep(1)

    _, o, _ = ssh.exec_command("journalctl -u nginx --no-pager | tail -n 20")
    print(o.read().decode())
    ssh.close()


if __name__ == "__main__":
    main()
