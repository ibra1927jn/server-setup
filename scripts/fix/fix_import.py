"""Fix and import the missing workflows into Hetzner n8n"""
import requests
import json
import os
from shared_config import N8N_URL, N8N_HEADERS

FLOWS_DIR = r"C:\AgenticOS\n8n-flows"
MISSING_FILES = ["server-sentinel.json", "ai-agent-base.json"]


def main():
    headers = N8N_HEADERS

    for f in MISSING_FILES:
        filepath = os.path.join(FLOWS_DIR, f)
        print(f"\n=== Importing {f} ===")

        with open(filepath, 'r', encoding='utf-8') as fh:
            raw_data = json.load(fh)

        # Strip everything except core properties n8n expects
        payload = {
            "name": raw_data.get("name", f.replace('.json', '')),
            "nodes": raw_data.get("nodes", []),
            "connections": raw_data.get("connections", {}),
            "settings": raw_data.get("settings", {}),
            "staticData": raw_data.get("staticData", None),
            "tags": raw_data.get("tags", [])
        }

        resp = requests.post(
            f"{N8N_URL}/api/v1/workflows",
            headers=headers,
            json=payload
        )
        print(f"  Status: {resp.status_code}")

        if resp.status_code in [200, 201]:
            result = resp.json()
            wf_id = result.get('id', 'unknown')
            print(f"  ✅ Created! ID: {wf_id}")

            # Activate it
            requests.patch(f"{N8N_URL}/api/v1/workflows/{wf_id}", headers=headers, json={"active": True})
            print("  ✅ Activated")
        else:
            print(f"  ❌ Error: {resp.text[:300]}")

    print("\n=== FINAL VERIFICATION ===")
    resp = requests.get(f"{N8N_URL}/api/v1/workflows", headers=headers)
    if resp.status_code == 200:
        workflows = resp.json().get('data', [])
        for wf in workflows:
            print(f"  - {wf.get('name')} | ID: {wf.get('id')} | Active: {wf.get('active')}")
        print(f"Total: {len(workflows)} workflows")


if __name__ == "__main__":
    main()
