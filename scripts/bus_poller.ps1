# ============================================
#  Antigravity Agent Bus Poller v2.0
#  Polls: GET  http://95.217.158.7/api/agent-bus/status
#  Done:  POST http://95.217.158.7/api/agent-bus/complete
# ============================================

$BUS_API      = "http://95.217.158.7/api/agent-bus"
$STATUS_URL   = "$BUS_API/status"
$COMPLETE_URL = "$BUS_API/complete"
$POLL_INTERVAL = 30            # seconds between polls
$processedIds  = [System.Collections.Generic.HashSet[string]]::new()

# --- Banner ---
Clear-Host
Write-Host ""
Write-Host "  ╔══════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "  ║   ANTIGRAVITY  ·  Agent Bus Poller v2    ║" -ForegroundColor Cyan
Write-Host "  ╚══════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Endpoint : $STATUS_URL" -ForegroundColor DarkGray
Write-Host "  Interval : ${POLL_INTERVAL}s" -ForegroundColor DarkGray
Write-Host "  Started  : $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  Waiting for tasks from Claude Code / n8n..." -ForegroundColor Yellow
Write-Host ""

# --- Helper: mark a task as done ---
function Complete-Task {
    param([string]$TaskId)
    try {
        $body = @{ id = $TaskId } | ConvertTo-Json -Compress
        Invoke-RestMethod -Uri $COMPLETE_URL -Method POST `
                          -ContentType "application/json" `
                          -Body $body -ErrorAction Stop
        Write-Host "  [DONE] Task $TaskId marked as completed on the bus." -ForegroundColor Green
    }
    catch {
        Write-Host "  [WARN] Could not mark $TaskId as done: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# --- Main loop ---
while ($true) {
    try {
        $response = Invoke-RestMethod -Uri $STATUS_URL -Method GET `
                                      -ContentType "application/json" `
                                      -ErrorAction Stop

        # The API may return the queue under different keys — try both
        $pendingTasks = $null
        if ($null -ne $response.pending_for_antigravity) {
            $pendingTasks = @($response.pending_for_antigravity)
        }
        elseif ($null -ne $response.pending_for_claude_ai) {
            $pendingTasks = @($response.pending_for_claude_ai)
        }

        if ($null -ne $pendingTasks -and $pendingTasks.Count -gt 0) {
            foreach ($task in $pendingTasks) {
                if (-not $processedIds.Contains($task.id)) {
                    # Audio alert
                    [console]::beep(1200, 300)
                    [console]::beep(1500, 500)

                    Write-Host ""
                    Write-Host "  ╔══════════════════════════════════════════════════════╗" -ForegroundColor Black -BackgroundColor Yellow
                    Write-Host "  ║     NEW TASK ASSIGNED TO ANTIGRAVITY                 ║" -ForegroundColor Black -BackgroundColor Yellow
                    Write-Host "  ╚══════════════════════════════════════════════════════╝" -ForegroundColor Black -BackgroundColor Yellow
                    Write-Host ""
                    Write-Host "  Task ID  : $($task.id)" -ForegroundColor Cyan
                    Write-Host "  Project  : $($task.project)" -ForegroundColor Magenta
                    Write-Host "  Source   : $($task.source)" -ForegroundColor DarkCyan
                    Write-Host "  Time     : $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor DarkGray
                    Write-Host ""
                    Write-Host "  Instruction:" -ForegroundColor Green
                    Write-Host "  $($task.instruction)" -ForegroundColor White
                    Write-Host ""
                    Write-Host "  ──────────────────────────────────────────────────────" -ForegroundColor DarkGray
                    Write-Host "  Paste the instruction into Antigravity chat to execute." -ForegroundColor Yellow
                    Write-Host "  When done, run:  Complete-Task '$($task.id)'" -ForegroundColor DarkGray
                    Write-Host ""

                    $null = $processedIds.Add($task.id)
                }
            }
        }
    }
    catch {
        $ts = Get-Date -Format 'HH:mm:ss'
        Write-Host "  [$ts] Bus unreachable — retrying in ${POLL_INTERVAL}s..." -ForegroundColor DarkRed
    }

    Start-Sleep -Seconds $POLL_INTERVAL
}
