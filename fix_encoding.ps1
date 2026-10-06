$bytes = [System.IO.File]::ReadAllBytes('d:\MCP\run_audit.ps1')
$bom = [byte[]](239, 187, 191)
[System.IO.File]::WriteAllBytes('d:\MCP\run_audit.ps1', $bom + $bytes)
