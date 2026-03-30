from shared_config import get_ssh_client, N8N_BRIEFING_WORKFLOW_ID


def main():
    ssh = get_ssh_client()

    print("Executing workflow...")
    _, ex_o, ex_e = ssh.exec_command(f'docker exec n8n-n8n-1 n8n execute --id {N8N_BRIEFING_WORKFLOW_ID}')
    print("OUTPUT:")
    print(ex_o.read().decode())
    print("ERROR:")
    print(ex_e.read().decode())

    ssh.close()


if __name__ == "__main__":
    main()
