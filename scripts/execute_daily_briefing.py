import json

from shared_config import get_ssh_client


def find_workflow_id(workflows, name):
    """Find a workflow ID by name from a list of workflow dicts."""
    for wf in workflows:
        if wf.get('name') == name:
            return wf.get('id')
    return None


def main():
    ssh = get_ssh_client()

    # Get the ID of the Daily Briefing workflow
    _, o, _ = ssh.exec_command("docker exec n8n-n8n-1 n8n export:workflow --all")
    workflows_json = o.read().decode()

    try:
        data = json.loads(workflows_json)
        briefing_id = find_workflow_id(data, 'Daily Briefing')

        if briefing_id:
            print(f"Found Daily Briefing ID: {briefing_id}")
            print("Executing workflow...")
            _, ex_o, ex_e = ssh.exec_command(
                f'docker exec n8n-n8n-1 n8n execute --id {briefing_id}'
            )
            output = ex_o.read().decode()
            error = ex_e.read().decode()
            print("OUTPUT:")
            print(output)
            if error:
                print("ERROR:")
                print(error)
        else:
            print("Daily Briefing workflow not found")
    except Exception as e:
        print(f"Error parsing JSON: {e}")

    ssh.close()


if __name__ == "__main__":
    main()
