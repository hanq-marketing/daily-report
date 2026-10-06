using namespace System.IO
using namespace System.Text
using namespace System.Text.RegularExpressions

$transcript_path = 'C:\Users\quang\.gemini\antigravity-ide\brain\6468b358-bdcf-4c67-bc97-1f9471806425\.system_generated\logs\transcript.jsonl'

$original_lines = @{}
$reader = [StreamReader]::new($transcript_path, [Encoding]::UTF8)
while (($line = $reader.ReadLine()) -ne $null) {
    if ($line.Contains("File Path: ``file:///d:/MCP/run_audit.ps1``")) {
        # This is a view_file output block
        # Extract the content field
        if ($line -match '"content":\s*"(.*)"$') {
            $contentStr = $matches[1]
            # Unescape JSON string
            $contentStr = [Regex]::Unescape($contentStr)
            
            $contentLines = $contentStr -split "`n"
            foreach ($l in $contentLines) {
                if ($l -match '^(\d+):\s?(.*)$') {
                    $lineNum = [int]$matches[1]
                    $text = $matches[2]
                    $text = $text.TrimEnd("`r")
                    $original_lines[$lineNum] = $text
                }
            }
        }
    }
}
$reader.Close()

Write-Host "Found $($original_lines.Count) lines."

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
    [System.IO.File]::WriteAllLines('d:\MCP\run_audit_full.ps1', $outLines, $utf8Bom)
    Write-Host "Recovered $($outLines.Count) lines to run_audit_full.ps1"
}