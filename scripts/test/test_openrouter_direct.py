import time

from shared_config import OPENROUTER_API_KEY, get_ssh_client


def main():
    ssh = get_ssh_client()

    # Test OpenRouter API directly
    json_body = '{"model": "zhipuai/glm-4.5-air", "messages": [{"role": "user", "content": "Di solamente OK"}], "max_tokens": 50}'
    cmd = (
        f"curl -s https://openrouter.ai/api/v1/chat/completions"
        f' -H "Authorization: Bearer {OPENROUTER_API_KEY}"'
        f' -H "Content-Type: application/json"'
        f" -d '{json_body}' --max-time 30"
    )

    _, o, _ = ssh.exec_command(cmd)
    time.sleep(15)
    result = o.read().decode()
    print("=== OPENROUTER DIRECT TEST ===")
    print(result[:1000])

    ssh.close()


if __name__ == "__main__":
    main()
