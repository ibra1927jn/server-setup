@echo off
:: AgenticOS — n8n Auto-Start
:: Place this in shell:startup to auto-run n8n on login
start /min cmd /c "npx n8n start"
