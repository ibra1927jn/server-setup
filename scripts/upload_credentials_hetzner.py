"""Upload credentials to Hetzner n8n"""
import requests
import json
from shared_config import N8N_URL, N8N_HEADERS

CRED_FILE = r"C:\AgenticOS\credentials-export.json"

headers = N8N_HEADERS

with open(CRED_FILE, 'r', encoding='utf-8') as f:
    creds = json.load(f)

for c in creds:
    payload = {
        "name": c["name"],
        "type": c["type"],
        "data": c["data"]
    }
    
    # If the user's PC turns off, the Hetzner node won't reach localhost.
    # However, for now we just import it as is.
    # For Ollama, we might need to use Ngrok later if we don't install it on Hetzner.
    
    print(f"Uploading credential: {c['name']} ({c['type']})...")
    resp = requests.post(f"{N8N_URL}/api/v1/credentials", headers=headers, json=payload)
    
    if resp.status_code in [200, 201]:
        print(f"  ✅ Success - ID: {resp.json().get('id')}")
    else:
        print(f"  ❌ Error: {resp.text[:300]}")

print("\n=== UPLOAD COMPLETE ===")
