"""Import workflows to Hetzner n8n via REST API with API key"""
import requests
import json
import os
from shared_config import N8N_URL, N8N_HEADERS

FLOWS_DIR = r"C:\AgenticOS\n8n-flows"
FLOW_FILES = [
    "server-sentinel.json",
    "trade-digest.json",
    "crm-bridge.json",
    "ai-agent-base.json",
]

headers = N8N_HEADERS

# Test API access first
print("=== Testing API access ===")
resp = requests.get(f"{N8N_URL}/api/v1/workflows", headers=headers)
print(f"GET /workflows: {resp.status_code}")
if resp.status_code == 200:
    existing = resp.json().get('data', [])
    print(f"Existing workflows: {len(existing)}")
else:
    print(f"Error: {resp.text[:200]}")

# Import each workflow
created = []
for f in FLOW_FILES:
    filepath = os.path.join(FLOWS_DIR, f)
    print(f"\n=== Importing {f} ===")

    with open(filepath, 'r', encoding='utf-8') as fh:
        workflow_data = json.load(fh)

    # Remove id (let n8n assign new one)
    workflow_data.pop('id', None)

    # Ensure name is set
    name = workflow_data.get('name', f.replace('.json', ''))
    print(f"  Name: {name}")
    print(f"  Nodes: {len(workflow_data.get('nodes', []))}")

    resp = requests.post(
        f"{N8N_URL}/api/v1/workflows",
        headers=headers,
        json=workflow_data
    )
    print(f"  Status: {resp.status_code}")

    if resp.status_code in [200, 201]:
        result = resp.json()
        wf_id = result.get('id', 'unknown')
        print(f"  ✅ Created! ID: {wf_id}")
        created.append((name, wf_id))
    else:
        print(f"  ❌ Error: {resp.text[:300]}")

# Activate all workflows
print("\n=== Activating workflows ===")
for name, wf_id in created:
    resp = requests.patch(
        f"{N8N_URL}/api/v1/workflows/{wf_id}",
        headers=headers,
        json={"active": True}
    )
    status = "✅ Activated" if resp.status_code == 200 else f"⚠️ {resp.status_code}"
    print(f"  {name}: {status}")

# Final listing
print("\n=== Final workflow list ===")
resp = requests.get(f"{N8N_URL}/api/v1/workflows", headers=headers)
if resp.status_code == 200:
    workflows = resp.json().get('data', [])
    for wf in workflows:
        print(f"  - {wf.get('name')} | ID: {wf.get('id')} | Active: {wf.get('active')}")
    print(f"\nTotal: {len(workflows)} workflows")

print("\n=== IMPORT COMPLETE ===")
