$transcript_path = 'C:\Users\quang\.gemini\antigravity-ide\brain\6468b358-bdcf-4c67-bc97-1f9471806425\.system_generated\logs\transcript.jsonl'
$lines = Get-Content $transcript_path -Encoding UTF8

$original_lines = @{}

foreach ($line in $lines) {
    try {
        $data = ConvertFrom-Json $line
        if ($data.content -and $data.content -match 'File Path: `file:///d:/MCP/run_audit\.ps1`') {
            $contentLines = $data.content -split "`n"
            foreach ($l in $contentLines) {
                if ($l -match '^(\d+):\s(.*)$') {
                    $lineNum = [int]$matches[1]
                    $text = $matches[2]
                    $original_lines[$lineNum] = $text
                }
            }
        }
    } catch {}
}

if ($original_lines.Count -gt 0) {
    $maxLine = ($original_lines.Keys | Measure-Object -Maximum).Maximum
    $outLines = @()
    for ($i = 1; $i -le $maxLine; $i++) {
        if ($original_lines.ContainsKey($i)) {
            $outLines += $original_lines[$i]
        } else {
            $outLines += ""
        }
    }
    $utf8Bom = New-Object System.Text.UTF8Encoding($true)
    [System.IO.File]::WriteAllLines('d:\MCP\run_audit.ps1.recovered', $outLines, $utf8Bom)
    Write-Host "Recovered $($original_lines.Count) lines to run_audit.ps1.recovered"
} else {
    Write-Host "No lines found."
}