from shared_config import get_ssh_client, OPENROUTER_API_KEY

ssh = get_ssh_client()

# Check OpenRouter credit balance
cmd = f'''curl -s https://openrouter.ai/api/v1/auth/key \
  -H "Authorization: Bearer {OPENROUTER_API_KEY}"'''
_, o, _ = ssh.exec_command(cmd)
print("=== OPENROUTER ACCOUNT INFO ===")
print(o.read().decode())

ssh.close()
