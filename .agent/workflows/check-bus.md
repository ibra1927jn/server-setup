---
description: Check the Agent Bus for pending tasks assigned to Antigravity. Run this at the START of every conversation.
---

# Agent Bus Check

// turbo-all

**This workflow MUST be executed at the very beginning of every conversation, before doing anything else.**

1. Poll the agent bus for pending tasks:
```
Invoke-RestMethod -Uri "http://95.217.158.7/api/agent-bus/status" -Method GET | ConvertTo-Json -Depth 10 | Out-File -FilePath "c:\Users\ibrab\Desktop\set up\bus_status.json" -Encoding UTF8 -Force
```

2. Read the file `c:\Users\ibrab\Desktop\set up\bus_status.json` and check the `pending_for_antigravity` array.

3. If there are pending tasks:
   - Display each task's **id**, **from**, **action**, **repo**, **summary**, and **body** to the user
   - Ask the user which tasks to execute
   - After completing a task, mark it as done:
```
Invoke-RestMethod -Uri "http://95.217.158.7/api/agent-bus/complete" -Method POST -ContentType "application/json" -Body '{"id":"THE_TASK_ID"}'
```

4. If there are no pending tasks, say: "📭 No pending tasks on the Agent Bus."

## Important Notes
- The bus endpoint is: `http://95.217.158.7/api/agent-bus/status`
- Complete endpoint is: `POST http://95.217.158.7/api/agent-bus/complete` with body `{"id": "task-id"}`
- Always use `Co-Authored-By: Antigravity <antigravity@google.com>` in git commits
- After pushing code, the bus automatically creates a review task for Claude Code
