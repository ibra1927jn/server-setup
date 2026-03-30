from shared_config import OPENROUTER_API_KEY, get_ssh_client


def main():
    ssh = get_ssh_client()

    # Check OpenRouter credit balance
    cmd = f'''curl -s https://openrouter.ai/api/v1/auth/key \
      -H "Authorization: Bearer {OPENROUTER_API_KEY}"'''
    _, o, _ = ssh.exec_command(cmd)
    print("=== OPENROUTER ACCOUNT INFO ===")
    print(o.read().decode())

    ssh.close()


if __name__ == "__main__":
    main()
