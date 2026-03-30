from shared_config import get_ssh_client

ssh = get_ssh_client()

# Get more specific error logs
grep_cmd = (
    "docker logs n8n-n8n-1 --tail=100 2>&1"
    " | grep -A2 -i"
    " 'error\\|fail\\|agent\\|openai"
    "\\|openrouter\\|glm\\|401\\|403\\|429\\|500'"
)
_, o, _ = ssh.exec_command(grep_cmd)
print(o.read().decode()[:3000])

ssh.close()
