"""Save diagnostic results to a file so we can read them without truncation"""
import time

from shared_config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, get_ssh_client


def main():
    ssh = get_ssh_client()

    bot = TELEGRAM_BOT_TOKEN
    chat_id = TELEGRAM_CHAT_ID

    # Run all diagnostics and save to file
    diag_script = f"""
echo "=== CURL TELEGRAM FROM SERVER ===" > /tmp/diag.txt
curl -s -X POST "https://api.telegram.org/bot{bot}/sendMessage" \\
  -H "Content-Type: application/json" \\
  -d '{{"chat_id": {chat_id}, "text": "HETZNER SERVER DIRECT TEST"}}' >> /tmp/diag.txt 2>&1

echo "" >> /tmp/diag.txt
echo "=== COINGECKO ===" >> /tmp/diag.txt
curl -s "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd" >> /tmp/diag.txt 2>&1

echo "" >> /tmp/diag.txt
echo "=== N8N CONTAINER TELEGRAM ===" >> /tmp/diag.txt
docker exec n8n-n8n-1 sh -c 'curl -s \
"https://api.telegram.org/bot{bot}/getMe" 2>/dev/null \
|| wget -q -O- "https://api.telegram.org/bot{bot}/getMe" \
2>/dev/null || echo "NO HTTP CLIENT IN CONTAINER"' \
>> /tmp/diag.txt 2>&1

echo "" >> /tmp/diag.txt
echo "=== N8N CONTAINER SEND MESSAGE ===" >> /tmp/diag.txt
docker exec n8n-n8n-1 sh -c 'curl -s -X POST \
"https://api.telegram.org/bot{bot}/sendMessage" \
-H "Content-Type: application/json" \
-d \\'{{"chat_id": {chat_id}, "text": "FROM N8N CONTAINER"}}\\' \
2>/dev/null || echo "CURL NOT AVAILABLE"' >> /tmp/diag.txt 2>&1

echo "" >> /tmp/diag.txt
echo "=== WORKFLOW LIST ===" >> /tmp/diag.txt
docker exec n8n-n8n-1 n8n list:workflow >> /tmp/diag.txt 2>&1

echo "DONE" >> /tmp/diag.txt
"""

    print("Running diagnostics on server...")
    _, o, e = ssh.exec_command(f"bash -c '{diag_script}'")
    o.read()
    e.read()

    time.sleep(5)

    # Read results
    print("\n=== RESULTS ===")
    _, o, _ = ssh.exec_command("cat /tmp/diag.txt")
    results = o.read().decode().strip()
    print(results)

    ssh.close()


if __name__ == "__main__":
    main()
