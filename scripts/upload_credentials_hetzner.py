"""Upload credentials to Hetzner n8n"""

import json

import requests
from shared_config import N8N_HEADERS, N8N_URL


def main():
    cred_file = r"C:\AgenticOS\credentials-export.json"

    headers = N8N_HEADERS

    with open(cred_file, encoding="utf-8") as f:
        creds = json.load(f)

    for c in creds:
        payload = {"name": c["name"], "type": c["type"], "data": c["data"]}

        print(f"Uploading credential: {c['name']} ({c['type']})...")
        resp = requests.post(f"{N8N_URL}/api/v1/credentials", headers=headers, json=payload, timeout=30)

        if resp.status_code in [200, 201]:
            print(f"  Success - ID: {resp.json().get('id')}")
        else:
            print(f"  Error: {resp.text[:300]}")

    print("\n=== UPLOAD COMPLETE ===")


if __name__ == "__main__":
    main()
