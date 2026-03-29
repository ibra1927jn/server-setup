"""Create OpenRouter (OpenAI-compatible) credential on Hetzner n8n"""
import requests
from shared_config import N8N_URL, N8N_HEADERS, OPENROUTER_API_KEY, VPS_HOST, VPS_USER, VPS_PASS

headers = N8N_HEADERS

# The credential type for OpenAI API
payload = {
    "name": "OpenRouter Account",
    "type": "openAiApi",
    "data": {
        "apiKey": OPENROUTER_API_KEY,
        "url": "https://openrouter.ai/api/v1"
    }
}

print("Creating OpenRouter credential...")
resp = requests.post(f"{N8N_URL}/api/v1/credentials", headers=headers, json=payload)

if resp.status_code in [200, 201]:
    res_data = resp.json()
    print(f"✅ Success! Credential ID: {res_data.get('id')}")
else:
    print(f"❌ Error: {resp.text}")

# Also create the correct SSH credential while we're at it, since the export format failed earlier
ssh_payload = {
    "name": "Hetzner SSH",
    "type": "sshPassword",
    "data": {
        "host": VPS_HOST,
        "port": 22,
        "username": VPS_USER,
        "password": VPS_PASS
    }
}

print("Creating Hetzner SSH credential...")
resp2 = requests.post(f"{N8N_URL}/api/v1/credentials", headers=headers, json=ssh_payload)

if resp2.status_code in [200, 201]:
    print(f"✅ SSH Success! Credential ID: {resp2.json().get('id')}")
else:
    print(f"❌ SSH Error: {resp2.text}")
