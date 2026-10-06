# Restore script: Rebuilds run_audit.ps1 from original content with fixes
# This repairs the encoding corruption caused by tool edits

$targetFile = "d:\MCP\run_audit.ps1"

# Read the corrupted file to get the structure - we'll fix the Vietnamese strings
$corruptedContent = [System.IO.File]::ReadAllText($targetFile, [System.Text.Encoding]::UTF8)

# Strategy: Replace ALL corrupted Vietnamese strings with correct ones
# Build a mapping of corrupted -> correct strings

$replacements = @{
    # Format-Currency function area
    '0 VN?' = '0 VNĐ'
    
    # Get-AdCritique function
    '?? C?NH BA?O D?T TI?N' = '🔴 CẢNH BÁO ĐỐT TIỀN'
    'Qu?ng c?o' = 'Quảng cáo'
    'da chi ti?u' = 'đã chi tiêu'
    'nhung chua t?o ra tin nh?n n?o' = 'nhưng chưa tạo ra tin nhắn nào'
    'T? l? chuy?n d?i b?ng 0' = 'Tỷ lệ chuyển đổi bằng 0'
    'C?n ki?m tra l?i li?n k?t tin nh?n' = 'Cần kiểm tra lại liên kết tin nhắn'
    'n?t g?i tin nh?n' = 'nút gửi tin nhắn'
    'tr?n Fanpage' = 'trên Fanpage'
    'ho?c n?i dung b?i vi?t' = 'hoặc nội dung bài viết'
    'xem c? b? m?u thu?n hay kh?ng' = 'xem có bị mâu thuẫn hay không'
}

# Actually, with so many corrupted strings across 1600 lines, individual replacement won't work well.
# Better approach: Read the corrupted bytes and try to reconstruct

Write-Host "The file has severe encoding corruption that cannot be automatically repaired."
Write-Host "The corrupted bytes (0x3F) have lost the original Unicode data."
Write-Host ""
Write-Host "RECOMMENDATION: Re-run the audit script directly inline to avoid file corruption."
Write-Host "Or download the original file from backup/source control."
