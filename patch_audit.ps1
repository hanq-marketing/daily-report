# Patch script to add timeout support to run_audit.ps1
# Reads the file with proper encoding and applies fix

$filePath = "d:\MCP\run_audit.ps1"

# Read file content as UTF-8
$content = [System.IO.File]::ReadAllText($filePath, [System.Text.Encoding]::UTF8)

# 1. Add TimeoutWebClient class after the Format-Currency function
$oldWebClient = @'
# UTF-8 REST API helper to preserve Vietnamese accents from Facebook API
function Invoke-RestMethodUtf8 ($uri) {
    try {
        $webClient = New-Object System.Net.WebClient
        $webClient.Encoding = [System.Text.Encoding]::UTF8
        $json = $webClient.DownloadString($uri)
        return ($json | ConvertFrom-Json)
    } catch {
        return (Invoke-RestMethod -Uri $uri -Method Get -TimeoutSec 20)
    }
}
'@

$newWebClient = @'
# Custom WebClient with timeout support
Add-Type -TypeDefinition @"
using System;
using System.Net;
public class TimeoutWebClient : WebClient
{
    public int TimeoutMs { get; set; }
    public TimeoutWebClient(int timeoutMs) { TimeoutMs = timeoutMs; }
    protected override WebRequest GetWebRequest(Uri address)
    {
        WebRequest request = base.GetWebRequest(address);
        request.Timeout = TimeoutMs;
        return request;
    }
}
"@ -ErrorAction SilentlyContinue

# UTF-8 REST API helper to preserve Vietnamese accents from Facebook API
function Invoke-RestMethodUtf8 ($uri) {
    try {
        $webClient = New-Object TimeoutWebClient(30000)
        $webClient.Encoding = [System.Text.Encoding]::UTF8
        $json = $webClient.DownloadString($uri)
        return ($json | ConvertFrom-Json)
    } catch {
        return (Invoke-RestMethod -Uri $uri -Method Get -TimeoutSec 30)
    }
}
'@

if ($content.Contains($oldWebClient)) {
    $content = $content.Replace($oldWebClient, $newWebClient)
    Write-Host "[+] Da them TimeoutWebClient (30s timeout)" -ForegroundColor Green
} else {
    Write-Host "[!] Khong tim thay doan code WebClient goc. Co the da duoc patch roi." -ForegroundColor Yellow
}

# 2. Add progress logging for API calls
$pairs = @(
    @{
        old = '        try {
            $campaignListUrl = "https://graph.facebook.com/v17.0/$($acc.id)/campaigns'
        new = '        try {
            Write-Host "    [1/4] Dang lay danh sach chien dich..." -ForegroundColor DarkGray
            $campaignListUrl = "https://graph.facebook.com/v17.0/$($acc.id)/campaigns'
    },
    @{
        old = '            # Fetch Ads and their Creatives
            $adsUrl = "https://graph.facebook.com/v17.0/$($acc.id)/ads'
        new = '            # Fetch Ads and their Creatives
            Write-Host "    [2/4] Dang lay thong tin quang cao & creative..." -ForegroundColor DarkGray
            $adsUrl = "https://graph.facebook.com/v17.0/$($acc.id)/ads'
    },
    @{
        old = '            # Fetch Campaign Insights
            $insightsUrl = "https://graph.facebook.com/v17.0/$($acc.id)/insights?level=campaign'
        new = '            # Fetch Campaign Insights
            Write-Host "    [3/4] Dang lay insights cap chien dich (14 ngay)..." -ForegroundColor DarkGray
            $insightsUrl = "https://graph.facebook.com/v17.0/$($acc.id)/insights?level=campaign'
    },
    @{
        old = '            # Fetch Ad-level Insights
            $adInsightsUrl = "https://graph.facebook.com/v17.0/$($acc.id)/insights?level=ad'
        new = '            # Fetch Ad-level Insights
            Write-Host "    [4/4] Dang lay insights cap quang cao..." -ForegroundColor DarkGray
            $adInsightsUrl = "https://graph.facebook.com/v17.0/$($acc.id)/insights?level=ad'
    }
)

foreach ($pair in $pairs) {
    if ($content.Contains($pair.old)) {
        $content = $content.Replace($pair.old, $pair.new)
        Write-Host "[+] Da them progress logging" -ForegroundColor Green
    }
}

# Write back with UTF-8 BOM encoding
$utf8Bom = New-Object System.Text.UTF8Encoding($true)
[System.IO.File]::WriteAllText($filePath, $content, $utf8Bom)

Write-Host "`n[OK] Da patch xong file run_audit.ps1 voi UTF-8 BOM encoding!" -ForegroundColor Cyan
