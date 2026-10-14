import csv
import sys
import time
import gspread
from google.oauth2.service_account import Credentials

sys.stdout.reconfigure(encoding='utf-8')

SHEET_URL = "https://docs.google.com/spreadsheets/d/1PD3zhqZ2rTZlMi7X3lsCh6fkvNcR-B2kGv0m9L0Fl_4/edit"
SERVICE_ACCOUNT_FILE = "d:\\MCP\\google_service_account.json"
CSV_FILE = "d:\\MCP\\data\\bao_cao_cac_tai_khoan_10_2026.csv"

def format_row(r, headers, col_map):
    formatted = []
    for h in headers:
        csv_col = col_map.get(h, h)
        val = r.get(csv_col, "")
        if h in ["Chi tiêu", "CTR (%)", "CPC", "CPM", "CPA"]:
            try: formatted.append(float(val))
            except: formatted.append(0.0)
        elif h in ["Hiển thị", "Click link", "Tin nhắn", "Lead", "Đăng ký", "Sđt theo campain"]:
            try: formatted.append(int(float(val)))
            except: formatted.append(0)
        else:
            formatted.append(str(val))
    return formatted

def run_sync():
    print("[1] Đọc dữ liệu từ file CSV...")
    csv_rows = []
    with open(CSV_FILE, mode='r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for r in reader:
            csv_rows.append(r)
    print(f"-> Đã đọc {len(csv_rows)} dòng dữ liệu từ CSV.")

    print("\n[2] Kết nối Google Sheets qua Service Account...")
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scopes)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_url(SHEET_URL)
    print(f"-> Đã kết nối thành công: '{spreadsheet.title}'")

    master_headers = [
        "Account Name", "Account ID", "Ngày", "Campaign ID", "Tên chiến dịch", 
        "Trạng thái", "Ngân sách/ngày", "Chi tiêu", "Hiển thị", "Click link", 
        "CTR (%)", "CPC", "CPM", "Tin nhắn", "Lead", "Đăng ký", "CPA", 
        "Cập nhật lúc", "ID quảng cáo", "Tên quảng cáo", "Sđt theo campain", "Tags Pancake"
    ]

    account_headers = [
        "Ngày", "Campaign ID", "Tên chiến dịch", 
        "Trạng thái", "Ngân sách/ngày", "Chi tiêu", "Hiển thị", "Click link", 
        "CTR (%)", "CPC", "CPM", "Tin nhắn", "Lead", "Đăng ký", "CPA", 
        "Cập nhật lúc", "ID quảng cáo", "Tên quảng cáo", "Sđt theo campain", "Tags Pancake"
    ]

    csv_to_master_map = {
        "Account Name": "Tài khoản",
        "Account ID": "ID tài khoản",
        "Ngày": "Ngày",
        "Campaign ID": "Campaign ID",
        "Tên chiến dịch": "Tên chiến dịch",
        "Trạng thái": "Trạng thái",
        "Ngân sách/ngày": "Ngân sách/ngày",
        "Chi tiêu": "Chi tiêu",
        "Hiển thị": "Hiển thị",
        "Click link": "Click link",
        "CTR (%)": "CTR (%)",
        "CPC": "CPC",
        "CPM": "CPM",
        "Tin nhắn": "Tin nhắn",
        "Lead": "Lead",
        "Đăng ký": "Đăng ký",
        "CPA": "CPA",
        "Cập nhật lúc": "Cập nhật lúc",
        "ID quảng cáo": "ID quảng cáo",
        "Tên quảng cáo": "Tên quảng cáo",
        "Sđt theo campain": "Sđt theo campain",
        "Tags Pancake": "Tags Pancake"
    }

    # 1. CẬP NHẬT TAB MASTER DATA (UPSERT: CẬP NHẬT SỐ LIỆU MỚI & THÊM DÒNG MỚI, BẢO TOÀN LỊCH SỬ)
    print("\n[3] Đối soát và cập nhật tab 'Master Data' (Cập nhật số liệu mới nhất & bảo toàn lịch sử)...")
    try:
        ws_master = spreadsheet.worksheet("Master Data")
    except gspread.exceptions.WorksheetNotFound:
        ws_master = spreadsheet.add_worksheet(title="Master Data", rows="2000", cols="25")
        ws_master.update([master_headers], "A1", value_input_option="USER_ENTERED")
        ws_master.format("A1:V1", {"textFormat": {"bold": True}})

    existing_master = ws_master.get_all_values()
    if not existing_master:
        existing_master = [master_headers]

    m_headers = existing_master[0]
    m_acc_idx = m_headers.index("Account ID") if "Account ID" in m_headers else 1
    m_date_idx = m_headers.index("Ngày") if "Ngày" in m_headers else 2
    m_camp_idx = m_headers.index("Campaign ID") if "Campaign ID" in m_headers else 3
    m_ad_idx = m_headers.index("ID quảng cáo") if "ID quảng cáo" in m_headers else 18

    # Bản đồ vị trí dòng cũ: key -> row_idx (trong existing_master)
    existing_row_indices = {}
    for idx, row in enumerate(existing_master[1:], start=1):
        if len(row) > max(m_acc_idx, m_date_idx):
            a_id = row[m_acc_idx].strip()
            d_val = row[m_date_idx].strip()
            c_id = row[m_camp_idx].strip() if len(row) > m_camp_idx else ""
            ad_id = row[m_ad_idx].strip() if len(row) > m_ad_idx else ""
            existing_row_indices[(a_id, d_val, c_id, ad_id)] = idx

    updated_master = [list(r) for r in existing_master]
    updated_master[0] = master_headers

    m_updated = 0
    m_added = 0

    for r in csv_rows:
        key = (
            r.get("ID tài khoản", "").strip(),
            r.get("Ngày", "").strip(),
            r.get("Campaign ID", "").strip(),
            r.get("ID quảng cáo", "").strip()
        )
        formatted_row = format_row(r, master_headers, csv_to_master_map)

        if key in existing_row_indices:
            idx = existing_row_indices[key]
            updated_master[idx] = formatted_row
            m_updated += 1
        else:
            updated_master.append(formatted_row)
            existing_row_indices[key] = len(updated_master) - 1
            m_added += 1

    ws_master.update(updated_master, "A1", value_input_option="USER_ENTERED")
    ws_master.format("A1:V1", {"textFormat": {"bold": True}})
    print(f"-> Tab 'Master Data': Đã cập nhật {m_updated} dòng và thêm mới {m_added} dòng (Tổng: {len(updated_master)-1} dòng).")

    # 2. CẬP NHẬT CÁC TAB TÀI KHOẢN RIÊNG
    print("\n[4] Đối soát và cập nhật các tab riêng của từng tài khoản...")
    existing_ws = {ws.title: ws for ws in spreadsheet.worksheets()}
    
    acc_rows_map = {}
    for r in csv_rows:
        aid = r.get("ID tài khoản", "")
        acc_rows_map.setdefault(aid, []).append(r)

    for title, ws in existing_ws.items():
        if title == "Master Data":
            continue
            
        print(f"\n* Đang kiểm tra tab '{title}'...")
        existing_acc_values = ws.get_all_values()
        
        if not existing_acc_values:
            existing_acc_values = [account_headers]
            
        acc_hdrs = existing_acc_values[0]
        date_idx = acc_hdrs.index("Ngày") if "Ngày" in acc_hdrs else 0
        camp_idx = acc_hdrs.index("Campaign ID") if "Campaign ID" in acc_hdrs else 1
        ad_idx = acc_hdrs.index("ID quảng cáo") if "ID quảng cáo" in acc_hdrs else 16

        existing_acc_indices = {}
        for idx, row in enumerate(existing_acc_values[1:], start=1):
            if len(row) > max(date_idx, camp_idx):
                d_val = row[date_idx].strip()
                c_id = row[camp_idx].strip() if len(row) > camp_idx else ""
                ad_id = row[ad_idx].strip() if len(row) > ad_idx else ""
                existing_acc_indices[(d_val, c_id, ad_id)] = idx

        matched_aid = None
        for aid in acc_rows_map.keys():
            if aid in title:
                matched_aid = aid
                break

        updated_acc = [list(r) for r in existing_acc_values]
        updated_acc[0] = account_headers
        a_updated = 0
        a_added = 0

        if matched_aid and matched_aid in acc_rows_map:
            for r in acc_rows_map[matched_aid]:
                key = (
                    r.get("Ngày", "").strip(),
                    r.get("Campaign ID", "").strip(),
                    r.get("ID quảng cáo", "").strip()
                )
                formatted_row = format_row(r, account_headers, {})

                if key in existing_acc_indices:
                    idx = existing_acc_indices[key]
                    updated_acc[idx] = formatted_row
                    a_updated += 1
                else:
                    updated_acc.append(formatted_row)
                    existing_acc_indices[key] = len(updated_acc) - 1
                    a_added += 1

        ws.update(updated_acc, "A1", value_input_option="USER_ENTERED")
        ws.format("A1:T1", {"textFormat": {"bold": True}})
        print(f"  -> Tab '{title}': Đã cập nhật {a_updated} dòng và thêm mới {a_added} dòng (Tổng: {len(updated_acc)-1} dòng).")
        time.sleep(1)

    print("\n✅ HOÀN TẤT ĐỒNG BỘ: SỐ LIỆU ĐÃ ĐƯỢC CẬP NHẬT MỚI NHẤT, DỮ LIỆU LỊCH SỬ ĐƯỢC BẢO TOÀN!")

if __name__ == "__main__":
    run_sync()
