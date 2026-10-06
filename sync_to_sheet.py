import os
import json
import glob
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')
import gspread
from google.oauth2.service_account import Credentials

SHEET_URL = "https://docs.google.com/spreadsheets/d/1PD3zhqZ2rTZlMi7X3lsCh6fkvNcR-B2kGv0m9L0Fl_4/edit"
SERVICE_ACCOUNT_FILE = "d:\\MCP\\google_service_account.json"
DATA_ROOT = "d:\\MCP\\data"

COLUMNS = [
    "Account Name", "Account ID", "Ngày", "Campaign ID", "Tên chiến dịch", 
    "Trạng thái", "Ngân sách/ngày", "Chi tiêu", "Hiển thị", "Click link", 
    "CTR", "CPC", "CPM", "Tin nhắn", "Lead", "Đăng ký", "CPA", "Cập nhật lúc"
]

def format_currency(value):
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0

def get_latest_data_dir():
    dirs = glob.glob(os.path.join(DATA_ROOT, "*"))
    dirs = [d for d in dirs if os.path.isdir(d)]
    if not dirs:
        return None
    return max(dirs, key=os.path.getmtime)

def parse_actions(actions_list):
    metrics = {"tin_nhan": 0, "lead": 0, "dang_ky": 0}
    if not actions_list:
        return metrics
    for a in actions_list:
        atype = a.get("action_type", "")
        val = int(a.get("value", 0))
        if atype in ["onsite_conversion.messaging_conversation_started_7d", "messaging_conversation_started_7d"]:
            metrics["tin_nhan"] += val
        elif atype in ["lead", "onsite_conversion.lead", "onsite_web_lead"]:
            metrics["lead"] += val
        elif atype in ["complete_registration", "omni_complete_registration", "offsite_conversion.fb_pixel_complete_registration"]:
            metrics["dang_ky"] += val
    return metrics

def sync_data():
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        print(f"[-] Không tìm thấy file {SERVICE_ACCOUNT_FILE}. Vui lòng tạo Service Account và lưu vào đây.")
        return

    print("[*] Đang kết nối tới Google Sheets...")
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scopes)
    client = gspread.authorize(creds)
    sheet = client.open_by_url(SHEET_URL)

    latest_dir = get_latest_data_dir()
    if not latest_dir:
        print("[-] Không tìm thấy thư mục data nào.")
        return
    print(f"[*] Đọc dữ liệu từ thư mục mới nhất: {latest_dir}")

    accounts_file = os.path.join(latest_dir, "ad_accounts.json")
    if not os.path.exists(accounts_file):
        print("[-] Không tìm thấy file ad_accounts.json.")
        return

    with open(accounts_file, "r", encoding="utf-8") as f:
        acc_data = json.load(f)
    accounts = acc_data.get("data", [])

    tab_name = "Master Data"
    try:
        worksheet = sheet.worksheet(tab_name)
    except gspread.exceptions.WorksheetNotFound:
        print(f"    [+] Tạo tab mới: {tab_name}")
        worksheet = sheet.add_worksheet(title=tab_name, rows="1000", cols="20")
        worksheet.append_row(COLUMNS)
        worksheet.format("A1:R1", {"textFormat": {"bold": True}})

    existing_records = worksheet.get_all_values()
    
    # Build map of existing rows by (Account ID, Date, Campaign ID) -> row_index (0-based)
    row_map = {}
    for i, row in enumerate(existing_records):
        if i == 0: continue # Skip header
        if len(row) >= 4:
            key = f"{row[1]}_{row[2]}_{row[3]}"
            row_map[key] = i
            
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    updates = []
    appends = []

    for acc in accounts:
        acc_id = acc.get("id")
        acc_name = acc.get("name", "Unknown")
        
        camp_file = os.path.join(latest_dir, f"{acc_id}_campaigns.json")
        ins_file = os.path.join(latest_dir, f"{acc_id}_campaign_insights_14d.json")
        
        if not os.path.exists(camp_file) or not os.path.exists(ins_file):
            continue
            
        print(f"[*] Xử lý tài khoản: {acc_name}")
        
        with open(camp_file, "r", encoding="utf-8") as f:
            camps = json.load(f).get("data", [])
        camp_map = {c["id"]: c for c in camps}
        
        with open(ins_file, "r", encoding="utf-8") as f:
            insights = json.load(f).get("data", [])
            
        if not insights:
            continue
        
        for ins in insights:
            c_id = ins.get("campaign_id")
            c_date = ins.get("date_start")
            key = f"{acc_id}_{c_date}_{c_id}"
            
            c_info = camp_map.get(c_id, {})
            c_status = c_info.get("status", "")
            c_budget = float(c_info.get("daily_budget", 0)) if c_info.get("daily_budget") else 0
            
            spend = float(ins.get("spend", 0))
            impressions = int(ins.get("impressions", 0))
            clicks = int(ins.get("inline_link_clicks", 0))
            
            ctr = (clicks / impressions * 100) if impressions > 0 else 0
            cpc = (spend / clicks) if clicks > 0 else 0
            cpm = (spend / impressions * 1000) if impressions > 0 else 0
            
            metrics = parse_actions(ins.get("actions", []))
            
            cpa = (spend / metrics["tin_nhan"]) if metrics["tin_nhan"] > 0 else 0
            
            row_data = [
                acc_name,
                acc_id,
                c_date,
                c_id,
                ins.get("campaign_name", ""),
                c_status,
                c_budget,
                spend,
                impressions,
                clicks,
                round(ctr, 2),
                round(cpc, 0),
                round(cpm, 0),
                metrics["tin_nhan"],
                metrics["lead"],
                metrics["dang_ky"],
                round(cpa, 0),
                now_str
            ]
            
            if key in row_map:
                row_idx = row_map[key]
                updates.append({
                    'range': f'A{row_idx + 1}:R{row_idx + 1}',
                    'values': [row_data]
                })
            else:
                appends.append(row_data)
                
    if updates:
        print(f"    [*] Cập nhật {len(updates)} dòng...")
        worksheet.batch_update(updates)
        
    if appends:
        print(f"    [*] Thêm mới {len(appends)} dòng...")
        worksheet.append_rows(appends)

    print("[+] Hoàn tất đẩy dữ liệu lên Google Sheets.")

if __name__ == "__main__":
    sync_data()
