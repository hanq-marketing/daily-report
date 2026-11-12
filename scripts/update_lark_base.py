import csv
import json
import os
import sys
import time
import requests
from datetime import datetime, timedelta, timezone

sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_FILE = os.path.join(BASE_DIR, ".env")
CSV_FILE = os.path.join(BASE_DIR, "data", "bao_cao_cac_tai_khoan_10_2026.csv")
LARK_HOST = "https://open.larksuite.com"

NUM_FLOAT_FIELDS = {"Chi tiêu", "CTR (%)", "CPC", "CPM", "CPA"}
NUM_INT_FIELDS = {"Hiển thị", "Click link", "Tin nhắn", "Lead", "Đăng ký", "Sđt theo campain"}

MASTER_FIELDS = [
    ("Account Name", 1),
    ("Account ID", 1),
    ("Ngày", 1),
    ("Campaign ID", 1),
    ("Tên chiến dịch", 1),
    ("Sản phẩm", 1),
    ("Trạng thái", 1),
    ("Ngân sách/ngày", 1),
    ("Chi tiêu", 2),
    ("Hiển thị", 2),
    ("Click link", 2),
    ("CTR (%)", 2),
    ("CPC", 2),
    ("CPM", 2),
    ("Tin nhắn", 2),
    ("Lead", 2),
    ("Đăng ký", 2),
    ("CPA", 2),
    ("Cập nhật lúc", 1),
    ("ID quảng cáo", 1),
    ("Tên quảng cáo", 1),
    ("Sđt theo campain", 2),
    ("Tags Pancake", 1),
    ("Nhãn chiến dịch", 1),
    ("Link bài quảng cáo", 1),
]

ACCOUNT_FIELDS = [
    ("Ngày", 1),
    ("Campaign ID", 1),
    ("Tên chiến dịch", 1),
    ("Sản phẩm", 1),
    ("Trạng thái", 1),
    ("Ngân sách/ngày", 1),
    ("Chi tiêu", 2),
    ("Hiển thị", 2),
    ("Click link", 2),
    ("CTR (%)", 2),
    ("CPC", 2),
    ("CPM", 2),
    ("Tin nhắn", 2),
    ("Lead", 2),
    ("Đăng ký", 2),
    ("CPA", 2),
    ("Cập nhật lúc", 1),
    ("ID quảng cáo", 1),
    ("Tên quảng cáo", 1),
    ("Sđt theo campain", 2),
    ("Tags Pancake", 1),
    ("Nhãn chiến dịch", 1),
    ("Link bài quảng cáo", 1),
]

CSV_TO_MASTER_MAP = {
    "Account Name": "Tài khoản",
    "Account ID": "ID tài khoản",
}


def load_env():
    env = {}
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            for line in f:
                s = line.strip()
                if s and not s.startswith("#") and "=" in s:
                    k, v = s.split("=", 1)
                    env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def get_tenant_token(app_id, app_secret):
    url = f"{LARK_HOST}/open-apis/auth/v3/tenant_access_token/internal"
    resp = requests.post(url, json={"app_id": app_id, "app_secret": app_secret}, timeout=20).json()
    if resp.get("code") != 0:
        raise RuntimeError(f"Lỗi lấy tenant_access_token: {resp}")
    return resp["tenant_access_token"]


def get_tables(app_token, headers):
    url = f"{LARK_HOST}/open-apis/bitable/v1/apps/{app_token}/tables"
    resp = requests.get(url, headers=headers, params={"page_size": 100}, timeout=20).json()
    if resp.get("code") != 0:
        raise RuntimeError(f"Lỗi lấy danh sách bảng: {resp}")
    return (resp.get("data") or {}).get("items", [])


def create_table(app_token, headers, table_name, field_defs):
    url = f"{LARK_HOST}/open-apis/bitable/v1/apps/{app_token}/tables"
    payload = {
        "table": {
            "name": table_name,
            "default_view_name": "Grid View",
            "fields": [{"field_name": name, "type": ftype} for name, ftype in field_defs],
        }
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=30).json()
    if resp.get("code") != 0:
        raise RuntimeError(f"Lỗi tạo bảng '{table_name}': {resp}")
    return resp["data"]["table_id"]


def ensure_fields(app_token, table_id, headers, field_defs):
    """Đảm bảo đủ cột; trả về tập tên các cột kiểu Date (type 5) trên bảng."""
    url = f"{LARK_HOST}/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/fields"
    resp = requests.get(url, headers=headers, params={"page_size": 100}, timeout=20).json()
    items = (resp.get("data") or {}).get("items", [])
    existing = {it["field_name"] for it in items}
    for name, ftype in field_defs:
        if name not in existing:
            requests.post(url, headers=headers, json={"field_name": name, "type": ftype}, timeout=20)
    return {it["field_name"]: it.get("type") for it in items}


TZ7 = timezone(timedelta(hours=7))


def date_to_ms(val):
    s = str(val or "").strip()
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%d/%m/%Y", "%d/%m/%Y %H:%M:%S"):
        try:
            return int(datetime.strptime(s, fmt).replace(tzinfo=TZ7).timestamp() * 1000)
        except ValueError:
            continue
    return None


def key_date(val):
    """Chuẩn hóa giá trị cột Ngày (timestamp hoặc chuỗi) về 'YYYY-MM-DD'."""
    if isinstance(val, (int, float)):
        return datetime.fromtimestamp(val / 1000, TZ7).strftime("%Y-%m-%d")
    return str_cell(val)


def fetch_all_records(app_token, table_id, headers):
    url = f"{LARK_HOST}/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records"
    items = []
    page_token = None
    while True:
        params = {"page_size": 500}
        if page_token:
            params["page_token"] = page_token
        resp = requests.get(url, headers=headers, params=params, timeout=30).json()
        if resp.get("code") != 0:
            raise RuntimeError(f"Lỗi đọc records bảng {table_id}: {resp}")
        data = resp.get("data") or {}
        items.extend(data.get("items") or [])
        if not data.get("has_more"):
            break
        page_token = data.get("page_token")
    return items


def format_record_fields(csv_row, field_defs, col_map, field_types=None):
    field_types = field_types or {}
    fields = {}
    for fname, _ in field_defs:
        csv_col = col_map.get(fname, fname)
        raw_val = csv_row.get(csv_col, "")
        ftype = field_types.get(fname)
        if ftype == 5:
            ms = date_to_ms(raw_val)
            if ms is not None:
                fields[fname] = ms
        elif ftype == 15:
            link = str(raw_val or "").strip()
            fields[fname] = {"link": link, "text": link} if link.startswith("http") else None
        elif fname in NUM_FLOAT_FIELDS:
            try:
                fields[fname] = float(raw_val)
            except Exception:
                fields[fname] = 0.0
        elif fname in NUM_INT_FIELDS:
            try:
                fields[fname] = int(float(raw_val))
            except Exception:
                fields[fname] = 0
        else:
            fields[fname] = str(raw_val) if raw_val is not None else ""
    return fields


def str_cell(val):
    if val is None:
        return ""
    if isinstance(val, list):
        return "".join(str(x.get("text", x)) if isinstance(x, dict) else str(x) for x in val).strip()
    return str(val).strip()


def batch_create_records(app_token, table_id, headers, records_list):
    if not records_list:
        return
    url = f"{LARK_HOST}/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create"
    for i in range(0, len(records_list), 500):
        chunk = records_list[i : i + 500]
        resp = requests.post(url, headers=headers, json={"records": chunk}, timeout=60).json()
        if resp.get("code") != 0:
            raise RuntimeError(f"Lỗi batch_create trên bảng {table_id}: {resp}")
        time.sleep(0.2)


def batch_update_records(app_token, table_id, headers, records_list):
    if not records_list:
        return
    url = f"{LARK_HOST}/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_update"
    for i in range(0, len(records_list), 500):
        chunk = records_list[i : i + 500]
        resp = requests.post(url, headers=headers, json={"records": chunk}, timeout=60).json()
        if resp.get("code") != 0:
            raise RuntimeError(f"Lỗi batch_update trên bảng {table_id}: {resp}")
        time.sleep(0.2)


def run_lark_sync():
    print("[1] Đọc dữ liệu từ file CSV...")
    csv_rows = []
    with open(CSV_FILE, mode="r", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            csv_rows.append(r)
    print(f"-> Đã đọc {len(csv_rows)} dòng dữ liệu từ CSV.")

    env = load_env()
    app_id = env.get("LARK_APP_ID")
    app_secret = env.get("LARK_APP_SECRET")
    app_token = env.get("LARK_APP_TOKEN")

    print(f"\n[2] Kết nối Lark Base ({app_token})...")
    token = get_tenant_token(app_id, app_secret)
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    tables = get_tables(app_token, headers)
    table_map = {t["name"]: t["table_id"] for t in tables}
    print(f"-> Hiện có {len(table_map)} bảng trên Base: {list(table_map.keys())}")

    # ─── 1. ĐỒNG BỘ BẢNG MASTER DATA ──────────────────────────────────────────
    print("\n[3] Đồng bộ bảng 'Master Data'...")
    if "Master Data" not in table_map:
        master_tid = create_table(app_token, headers, "Master Data", MASTER_FIELDS)
        table_map["Master Data"] = master_tid
        print(f"  + Đã tạo mới bảng 'Master Data' ({master_tid})")
    else:
        master_tid = table_map["Master Data"]
    master_dates = ensure_fields(app_token, master_tid, headers, MASTER_FIELDS)

    # Xóa bảng mặc định 'Bảng' nếu còn tồn tại và rỗng
    if "Bảng" in table_map and len(table_map) > 1:
        default_tid = table_map["Bảng"]
        del_url = f"{LARK_HOST}/open-apis/bitable/v1/apps/{app_token}/tables/{default_tid}"
        del_resp = requests.delete(del_url, headers=headers, timeout=20).json()
        if del_resp.get("code") == 0:
            print(f"  - Đã dọn bảng trống mặc định 'Bảng' ({default_tid})")
            del table_map["Bảng"]

    existing_master_recs = fetch_all_records(app_token, master_tid, headers)
    master_index = {}
    for rec in existing_master_recs:
        flds = rec.get("fields") or {}
        key = (
            str_cell(flds.get("Account ID")),
            key_date(flds.get("Ngày")),
            str_cell(flds.get("Campaign ID")),
            str_cell(flds.get("ID quảng cáo")),
        )
        if any(key):
            master_index[key] = rec["record_id"]

    to_create_master = []
    to_update_master = []
    seen_master_keys = set()

    for r in csv_rows:
        key = (
            r.get("ID tài khoản", "").strip(),
            r.get("Ngày", "").strip(),
            r.get("Campaign ID", "").strip(),
            r.get("ID quảng cáo", "").strip(),
        )
        if key in seen_master_keys:
            continue
        seen_master_keys.add(key)

        fields_payload = format_record_fields(r, MASTER_FIELDS, CSV_TO_MASTER_MAP, master_dates)
        if key in master_index:
            to_update_master.append({"record_id": master_index[key], "fields": fields_payload})
        else:
            to_create_master.append({"fields": fields_payload})

    batch_update_records(app_token, master_tid, headers, to_update_master)
    batch_create_records(app_token, master_tid, headers, to_create_master)
    print(
        f"-> Bảng 'Master Data': Đã cập nhật {len(to_update_master)} dòng và thêm mới {len(to_create_master)} dòng "
        f"(Tổng: {len(existing_master_recs) + len(to_create_master)} dòng)."
    )

    # ─── 2. ĐỒNG BỘ CÁC BẢNG TÀI KHOẢN RIÊNG BIỆT ─────────────────────────────
    print("\n[4] Đồng bộ các bảng riêng của từng Tài khoản Ads...")
    acc_groups = {}
    for r in csv_rows:
        aname = r.get("Tài khoản", "").strip()
        aid = r.get("ID tài khoản", "").strip()
        if aname and aid:
            tname = f"{aname} ({aid})"
            acc_groups.setdefault(tname, []).append(r)

    # Đảm bảo thứ tự cố định như trên Google Sheets
    for tname, rows_list in acc_groups.items():
        if tname not in table_map:
            tid = create_table(app_token, headers, tname, ACCOUNT_FIELDS)
            table_map[tname] = tid
            print(f"  + Đã tạo bảng '{tname}' ({tid})")
        else:
            tid = table_map[tname]
        acc_dates = ensure_fields(app_token, tid, headers, ACCOUNT_FIELDS)

        existing_acc_recs = fetch_all_records(app_token, tid, headers)
        acc_index = {}
        for rec in existing_acc_recs:
            flds = rec.get("fields") or {}
            key = (
                key_date(flds.get("Ngày")),
                str_cell(flds.get("Campaign ID")),
                str_cell(flds.get("ID quảng cáo")),
            )
            if any(key):
                acc_index[key] = rec["record_id"]

        to_create_acc = []
        to_update_acc = []
        seen_acc_keys = set()

        for r in rows_list:
            key = (
                r.get("Ngày", "").strip(),
                r.get("Campaign ID", "").strip(),
                r.get("ID quảng cáo", "").strip(),
            )
            if key in seen_acc_keys:
                continue
            seen_acc_keys.add(key)

            fields_payload = format_record_fields(r, ACCOUNT_FIELDS, {}, acc_dates)
            if key in acc_index:
                to_update_acc.append({"record_id": acc_index[key], "fields": fields_payload})
            else:
                to_create_acc.append({"fields": fields_payload})

        batch_update_records(app_token, tid, headers, to_update_acc)
        batch_create_records(app_token, tid, headers, to_create_acc)
        print(
            f"  -> Bảng '{tname}': Cập nhật {len(to_update_acc)} dòng, thêm mới {len(to_create_acc)} dòng "
            f"(Tổng: {len(existing_acc_recs) + len(to_create_acc)} dòng)."
        )

    print("\n✅ HOÀN TẤT ĐỒNG BỘ DỮ LIỆU LÊN LARK BASE!")


if __name__ == "__main__":
    run_lark_sync()
