# ═══════════════════════════════════════════════════════════
# n8n-service.ps1 — AgenticOS n8n Background Service
# Runs n8n as a persistent background process on Windows
# ═══════════════════════════════════════════════════════════

$LogFile = "C:\AgenticOS\logs\n8n-service.log"
$PidFile = "C:\AgenticOS\logs\n8n.pid"

# Create logs directory
if (-not (Test-Path "C:\AgenticOS\logs")) {
    New-Item -ItemType Directory -Path "C:\AgenticOS\logs" -Force | Out-Null
}

# Kill any existing n8n process
$existingPid = $null
if (Test-Path $PidFile) {
    $existingPid = Get-Content $PidFile -ErrorAction SilentlyContinue
    if ($existingPid) {
        try {
            Stop-Process -Id $existingPid -Force -ErrorAction SilentlyContinue
            Write-Host "[$(Get-Date)] Stopped existing n8n (PID: $existingPid)"
        } catch {}
    }
}

# Start n8n in background
Write-Host "[$(Get-Date)] Starting n8n..."
$process = Start-Process -FilePath "npx" -ArgumentList "n8n", "start" `
    -WindowStyle Hidden `
    -RedirectStandardOutput $LogFile `
    -RedirectStandardError "$LogFile.err" `
    -PassThru

# Save PID
$process.Id | Out-File $PidFile -Force
Write-Host "[$(Get-Date)] n8n started (PID: $($process.Id))"
Write-Host "[$(Get-Date)] Log: $LogFile"
Write-Host "[$(Get-Date)] UI: http://localhost:5678"
