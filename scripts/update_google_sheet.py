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
        "Account Name", "Account ID", "Ngày", "Campaign ID", "Tên chiến dịch", "Sản phẩm",
        "Trạng thái", "Ngân sách/ngày", "Chi tiêu", "Hiển thị", "Click link", 
        "CTR (%)", "CPC", "CPM", "Tin nhắn", "Lead", "Đăng ký", "CPA", 
        "Cập nhật lúc", "ID quảng cáo", "Tên quảng cáo", "Sđt theo campain", "Tags Pancake", "Nhãn chiến dịch", "Link bài quảng cáo"
    ]

    account_headers = [
        "Ngày", "Campaign ID", "Tên chiến dịch", "Sản phẩm",
        "Trạng thái", "Ngân sách/ngày", "Chi tiêu", "Hiển thị", "Click link", 
        "CTR (%)", "CPC", "CPM", "Tin nhắn", "Lead", "Đăng ký", "CPA", 
        "Cập nhật lúc", "ID quảng cáo", "Tên quảng cáo", "Sđt theo campain", "Tags Pancake", "Nhãn chiến dịch", "Link bài quảng cáo"
    ]

    csv_to_master_map = {
        "Account Name": "Tài khoản",
        "Account ID": "ID tài khoản",
        "Ngày": "Ngày",
        "Campaign ID": "Campaign ID",
        "Tên chiến dịch": "Tên chiến dịch",
        "Sản phẩm": "Sản phẩm",
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
        "Tags Pancake": "Tags Pancake",
        "Nhãn chiến dịch": "Nhãn chiến dịch",
        "Link bài quảng cáo": "Link bài quảng cáo"
    }

    # 1. CẬP NHẬT TAB MASTER DATA (UPSERT: CẬP NHẬT SỐ LIỆU MỚI & THÊM DÒNG MỚI, BẢO TOÀN LỊCH SỬ)
    print("\n[3] Đối soát và cập nhật tab 'Master Data' (Cập nhật số liệu mới nhất & bảo toàn lịch sử)...")
    try:
        ws_master = spreadsheet.worksheet("Master Data")
    except gspread.exceptions.WorksheetNotFound:
        ws_master = spreadsheet.add_worksheet(title="Master Data", rows="3000", cols="26")
        ws_master.update([master_headers], "A1", value_input_option="USER_ENTERED")
        ws_master.format("A1:Y1", {"textFormat": {"bold": True}})

    existing_master = ws_master.get_all_values()
    if not existing_master:
        existing_master = [master_headers]

    m_headers = existing_master[0]
    m_acc_idx = m_headers.index("Account ID") if "Account ID" in m_headers else 1
    m_date_idx = m_headers.index("Ngày") if "Ngày" in m_headers else 2
    m_camp_idx = m_headers.index("Campaign ID") if "Campaign ID" in m_headers else 3
    m_ad_idx = m_headers.index("ID quảng cáo") if "ID quảng cáo" in m_headers else 19

    # Xây dựng danh sách rows từ CSV chuẩn 25 cột
    csv_keys = set()
    master_rows = [master_headers]
    for r in csv_rows:
        key = (
            r.get("ID tài khoản", "").strip(),
            r.get("Ngày", "").strip(),
            r.get("Campaign ID", "").strip(),
            r.get("ID quảng cáo", "").strip()
        )
        csv_keys.add(key)
        master_rows.append(format_row(r, master_headers, csv_to_master_map))

    # Nếu có dòng cũ trong existing_master mà không có trong CSV hiện tại (bảo toàn lịch sử cũ)
    old_preserved_count = 0
    if len(m_headers) >= len(master_headers):
        for row in existing_master[1:]:
            # Bỏ qua dòng bị lệch cột trước đó (Sản phẩm = CAMPAIGN_PAUSED)
            if len(row) > 5 and row[5] == "CAMPAIGN_PAUSED":
                continue
            if len(row) > max(m_acc_idx, m_date_idx):
                a_id = row[m_acc_idx].strip()
                d_val = row[m_date_idx].strip()
                c_id = row[m_camp_idx].strip() if len(row) > m_camp_idx else ""
                ad_id = row[m_ad_idx].strip() if len(row) > m_ad_idx else ""
                k = (a_id, d_val, c_id, ad_id)
                if k not in csv_keys and any(k):
                    # Đảm bảo đủ số cột
                    padded = list(row) + [""] * max(0, len(master_headers) - len(row))
                    master_rows.append(padded[:len(master_headers)])
                    old_preserved_count += 1

    ws_master.clear()
    ws_master.update(master_rows, "A1", value_input_option="USER_ENTERED")
    ws_master.format("A1:Y1", {"textFormat": {"bold": True}})
    print(f"-> Tab 'Master Data': Đã đồng bộ thành công {len(master_rows)-1} dòng (trong đó {len(csv_rows)} dòng mới/cập nhật, {old_preserved_count} dòng lịch sử bảo toàn).")

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

        acc_keys = set()
        updated_acc = [account_headers]
        if matched_aid and matched_aid in acc_rows_map:
            for r in acc_rows_map[matched_aid]:
                key = (
                    r.get("Ngày", "").strip(),
                    r.get("Campaign ID", "").strip(),
                    r.get("ID quảng cáo", "").strip()
                )
                acc_keys.add(key)
                updated_acc.append(format_row(r, account_headers, {}))

        # Giữ lại các dòng lịch sử cũ nếu có đủ số cột
        if len(acc_hdrs) >= len(account_headers):
            for row in existing_acc_values[1:]:
                if len(row) > max(date_idx, camp_idx):
                    d_val = row[date_idx].strip()
                    c_id = row[camp_idx].strip() if len(row) > camp_idx else ""
                    ad_id = row[ad_idx].strip() if len(row) > ad_idx else ""
                    k = (d_val, c_id, ad_id)
                    if k not in acc_keys and any(k):
                        padded = list(row) + [""] * max(0, len(account_headers) - len(row))
                        updated_acc.append(padded[:len(account_headers)])

        ws.clear()
        ws.update(updated_acc, "A1", value_input_option="USER_ENTERED")
        ws.format("A1:W1", {"textFormat": {"bold": True}})
        print(f"  -> Tab '{title}': Đã đồng bộ {len(updated_acc)-1} dòng.")
        time.sleep(1)

    print("\n✅ HOÀN TẤT ĐỒNG BỘ: SỐ LIỆU ĐÃ ĐƯỢC CẬP NHẬT MỚI NHẤT, DỮ LIỆU LỊCH SỬ ĐƯỢC BẢO TOÀN!")

if __name__ == "__main__":
    run_sync()
