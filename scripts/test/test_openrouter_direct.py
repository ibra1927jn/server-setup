import time
from shared_config import get_ssh_client, OPENROUTER_API_KEY

ssh = get_ssh_client()

# Test OpenRouter API directly
cmd = f'''curl -s https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer {OPENROUTER_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "zhipuai/glm-4.5-air",
    "messages": [{"role": "user", "content": "Di solamente OK"}],
    "max_tokens": 50
  }' --max-time 30'''

_, o, _ = ssh.exec_command(cmd)
time.sleep(15)
result = o.read().decode()
print("=== OPENROUTER DIRECT TEST ===")
print(result[:1000])

ssh.close()
