"""
Test directo: enviar mensaje a Telegram usando la API del bot.
Si esto no funciona, el problema es el token o el chatID.
"""
import json
from shared_config import get_ssh_client, TELEGRAM_CHAT_ID


def main():
    ssh = get_ssh_client()

    # Get the decrypted Telegram token
    print("=== Intentando obtener token de Telegram ===")
    _, o, _ = ssh.exec_command("docker exec n8n-n8n-1 n8n export:credentials --all --decrypted 2>/dev/null")
    raw = o.read().decode().strip()

    telegram_token = None
    try:
        creds = json.loads(raw)
        for c in creds:
            if "telegram" in c.get("type", "").lower():
                print(f"  Cred: {c.get('name')} (type: {c.get('type')})")
                data = c.get("data", {})
                if isinstance(data, dict):
                    telegram_token = data.get("botToken", data.get("accessToken", None))
                print(f"  Token: {str(telegram_token)[:20]}..." if telegram_token else "  Token: NOT FOUND")
    except Exception as ex:
        print(f"  Parse error: {ex}")
        print(f"  Raw: {raw[:200]}")

    if telegram_token:
        # Test 1: getMe
        print("\n=== Test getMe ===")
        cmd1 = f'curl -s "https://api.telegram.org/bot{telegram_token}/getMe"'
        _, o, _ = ssh.exec_command(cmd1)
        result = o.read().decode().strip()
        print(f"  {result[:200]}")

        # Test 2: sendMessage
        print("\n=== Test sendMessage ===")
        chat_id = TELEGRAM_CHAT_ID
        message = "Test AgenticOS - Si ves esto, Telegram funciona correctamente!"
        cmd2 = (
            f'curl -s -X POST'
            f' "https://api.telegram.org/bot{telegram_token}/sendMessage"'
            f' -d "chat_id={chat_id}&text={message}"'
        )
        _, o, _ = ssh.exec_command(cmd2)
        result2 = o.read().decode().strip()
        print(f"  {result2[:300]}")

        if '"ok":true' in result2:
            print("\n  TELEGRAM FUNCIONA! El mensaje se envio correctamente.")
        elif '"ok":false' in result2:
            r = json.loads(result2)
            print(f"\n  ERROR: {r.get('description', '?')}")

            # Maybe wrong chat ID? Try getUpdates
            print("\n=== getUpdates (para ver tu chatID real) ===")
            cmd3 = f'curl -s "https://api.telegram.org/bot{telegram_token}/getUpdates?limit=3"'
            _, o, _ = ssh.exec_command(cmd3)
            updates = o.read().decode().strip()
            print(f"  {updates[:400]}")
    else:
        print("\n  No se pudo obtener el token. Intentando via env vars...")
        _, o, _ = ssh.exec_command("docker exec n8n-n8n-1 env | grep -i telegram")
        print(o.read().decode().strip())

    # Also check n8n logs for the latest execution
    print("\n=== N8N LOGS (telegram related) ===")
    docker_log_cmd = (
        "docker logs n8n-n8n-1 --tail 50 2>&1"
        " | grep -i -E '(telegram|error|fail|cred)' | tail -10"
    )
    _, o, _ = ssh.exec_command(docker_log_cmd)
    logs = o.read().decode().strip()
    print(logs if logs else "  (no relevant logs)")

    ssh.close()
    print("\nDone!")


if __name__ == "__main__":
    main()
