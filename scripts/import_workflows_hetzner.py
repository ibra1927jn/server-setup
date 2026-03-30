"""Import workflows to Hetzner n8n via REST API with API key"""
import json
import os

import requests
from shared_config import N8N_HEADERS, N8N_URL

FLOWS_DIR = r"C:\AgenticOS\n8n-flows"
FLOW_FILES = [
    "server-sentinel.json",
    "trade-digest.json",
    "crm-bridge.json",
    "ai-agent-base.json",
]


def prepare_workflow(workflow_data, filename):
    """Remove id and ensure name is set for import."""
    workflow_data.pop('id', None)
    if 'name' not in workflow_data or not workflow_data['name']:
        workflow_data['name'] = filename.replace('.json', '')
    return workflow_data


def import_workflow(base_url, headers, workflow_data):
    """Import a single workflow via REST API. Returns (name, id) or None."""
    name = workflow_data.get('name', 'unknown')
    resp = requests.post(
        f"{base_url}/api/v1/workflows",
        headers=headers,
        json=workflow_data,
        timeout=30
    )
    if resp.status_code in [200, 201]:
        result = resp.json()
        return (name, result.get('id', 'unknown'))
    return None


def activate_workflow(base_url, headers, wf_id):
    """Activate a workflow by ID. Returns True on success."""
    resp = requests.patch(
        f"{base_url}/api/v1/workflows/{wf_id}",
        headers=headers,
        json={"active": True},
        timeout=30
    )
    return resp.status_code == 200


def main():
    headers = N8N_HEADERS

    # Test API access first
    print("=== Testing API access ===")
    resp = requests.get(f"{N8N_URL}/api/v1/workflows", headers=headers, timeout=30)
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

        with open(filepath, encoding='utf-8') as fh:
            workflow_data = json.load(fh)

        workflow_data = prepare_workflow(workflow_data, f)
        name = workflow_data['name']
        print(f"  Name: {name}")
        print(f"  Nodes: {len(workflow_data.get('nodes', []))}")

        result = import_workflow(N8N_URL, headers, workflow_data)
        if result:
            print(f"  Created! ID: {result[1]}")
            created.append(result)
        else:
            print(f"  Error importing {f}")

    # Activate all workflows
    print("\n=== Activating workflows ===")
    for name, wf_id in created:
        ok = activate_workflow(N8N_URL, headers, wf_id)
        status = "Activated" if ok else "Failed"
        print(f"  {name}: {status}")

    # Final listing
    print("\n=== Final workflow list ===")
    resp = requests.get(f"{N8N_URL}/api/v1/workflows", headers=headers, timeout=30)
    if resp.status_code == 200:
        workflows = resp.json().get('data', [])
        for wf in workflows:
            print(f"  - {wf.get('name')} | ID: {wf.get('id')} | Active: {wf.get('active')}")
        print(f"\nTotal: {len(workflows)} workflows")

    print("\n=== IMPORT COMPLETE ===")


if __name__ == "__main__":
    main()
