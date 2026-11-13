import urllib.request
import urllib.parse
import json
import csv
import sys
import os
import re
import time
from datetime import datetime, timezone, timedelta

sys.stdout.reconfigure(encoding='utf-8')

# ─── Load tokens từ .env ─────────────────────────────────────────────────────
FB_TOKEN = ""
PANCAKE_TOKEN = ""
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
with open(env_path, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line.startswith('FB_TOKEN='):
            FB_TOKEN = line.split('=', 1)[1].strip()
        elif line.startswith('PANCAKE_PAGE_ACCESS_TOKEN'):
            PANCAKE_TOKEN = line.split('=', 1)[1].strip()

PANCAKE_USER_BASE = "https://pages.fm/api/v1"
PANCAKE_PAGE_BASE = "https://pages.fm/api/public_api/v1"
PHONE_REGEX = re.compile(r'(?:0|\+84)[3|5|7|8|9][0-9]{8}\b')
VN_TZ = timezone(timedelta(hours=7))

# ─── XÁC ĐỊNH KHOẢNG THỜI GIAN CẬP NHẬT (INCREMENTAL HOẶC FULL) ───────────────
import argparse

parser = argparse.ArgumentParser(description="Facebook Ads & Pancake Multi-Account Daily Report")
parser.add_argument("--full", action="store_true", help="Buộc lấy toàn bộ dữ liệu lịch sử từ 2026-10-01")
parser.add_argument("--since", type=str, default="", help="Ngày bắt đầu (YYYY-MM-DD)")
parser.add_argument("--until", type=str, default="", help="Ngày kết thúc (YYYY-MM-DD)")
args, unknown = parser.parse_known_args()

CSV_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "bao_cao_cac_tai_khoan_10_2026.csv")
DEFAULT_HISTORICAL_START = "2026-10-01"
today_str = datetime.now(VN_TZ).strftime("%Y-%m-%d")

# 1. Đọc dữ liệu cũ hiện có từ file CSV để xác định mốc ngày
existing_rows = []
existing_dates = set()
if os.path.exists(CSV_FILE):
    try:
        with open(CSV_FILE, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for r in reader:
                d = r.get("Ngày", "").strip()
                if d and re.match(r'^\d{4}-\d{2}-\d{2}$', d):
                    existing_dates.add(d)
                existing_rows.append(r)
    except Exception as e:
        print(f"⚠️ Cảnh báo đọc file CSV hiện tại: {e}")

max_existing_date = max(existing_dates) if existing_dates else ""
min_existing_date = min(existing_dates) if existing_dates else ""

if args.since:
    SINCE_DATE = args.since
    UNTIL_DATE = args.until if args.until else today_str
    MODE_TEXT = f"TÙY CHỌN CLI: {SINCE_DATE} -> {UNTIL_DATE}"
elif args.full or not existing_rows or not max_existing_date:
    SINCE_DATE = DEFAULT_HISTORICAL_START
    UNTIL_DATE = today_str
    MODE_TEXT = f"FULL (TOÀN BỘ): {SINCE_DATE} -> {UNTIL_DATE} (Kéo lại toàn bộ lịch sử)"
else:
    # Tự động tính chênh lệch ngày giữa dữ liệu cũ và hôm nay
    today_dt = datetime.strptime(today_str, "%Y-%m-%d")
    max_dt = datetime.strptime(max_existing_date, "%Y-%m-%d")
    diff_days = (today_dt - max_dt).days

    if diff_days <= 0:
        # Dữ liệu đã có đến hôm nay: quét lại 2 ngày gần nhất (hôm qua & hôm nay) để cập nhật số liệu mới nhất trong ngày
        fetch_start_dt = max_dt - timedelta(days=1)
        SINCE_DATE = fetch_start_dt.strftime("%Y-%m-%d")
        UNTIL_DATE = today_str
        MODE_TEXT = f"INCREMENTAL: Quét làm mới hôm nay & hôm qua ({SINCE_DATE} -> {UNTIL_DATE}), bảo toàn dữ liệu cũ trước {SINCE_DATE}."
    else:
        # Dữ liệu thiếu diff_days ngày: quét từ (max_existing_date - 1 ngày) để bao quát ngày giáp ranh
        fetch_start_dt = max_dt - timedelta(days=1)
        SINCE_DATE = fetch_start_dt.strftime("%Y-%m-%d")
        UNTIL_DATE = today_str
        MODE_TEXT = f"INCREMENTAL: Bổ sung {diff_days} ngày còn thiếu ({SINCE_DATE} -> {UNTIL_DATE}), bảo toàn dữ liệu cũ trước {SINCE_DATE}."

print("\n" + "=" * 70)
print(f"📅 PHÂN TÍCH MỐC DỮ LIỆU CẬP NHẬT HÀNG NGÀY:")
if existing_rows:
    print(f"  - Dữ liệu hiện có: {len(existing_rows)} bản ghi ({min_existing_date} -> {max_existing_date})")
    print(f"  - Ngày mới nhất trong dữ liệu cũ: {max_existing_date}")
    print(f"  - Hôm nay: {today_str} (Chênh lệch: {(datetime.strptime(today_str, '%Y-%m-%d') - datetime.strptime(max_existing_date, '%Y-%m-%d')).days} ngày)")
else:
    print("  - Chưa có file dữ liệu cũ hoặc file rỗng.")
print(f"  -> {MODE_TEXT}")
print("=" * 70 + "\n")

since_ts = int(datetime.strptime(SINCE_DATE, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp())
until_ts = int(datetime.strptime(UNTIL_DATE, "%Y-%m-%d").replace(hour=23, minute=59, second=59, tzinfo=timezone.utc).timestamp())

# ─── Load Cấu hình Nhãn chiến dịch & Ad Creatives ──────────────────────────────
TAGS_CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "campaign_tags.json")
TAGS_CONFIG = {}
if os.path.exists(TAGS_CONFIG_FILE):
    try:
        with open(TAGS_CONFIG_FILE, "r", encoding="utf-8") as f:
            TAGS_CONFIG = json.load(f)
    except Exception as e:
        print(f"⚠️ Cảnh báo đọc campaign_tags.json: {e}")

AD_CREATIVES_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "ad_creatives_cache.json")
AD_CREATIVES = {}
if os.path.exists(AD_CREATIVES_FILE):
    try:
        with open(AD_CREATIVES_FILE, "r", encoding="utf-8") as f:
            AD_CREATIVES = json.load(f)
    except Exception as e:
        print(f"⚠️ Cảnh báo đọc ad_creatives_cache.json: {e}")

def get_campaign_tags(cid, cname, adname, aname, adid=None, ad_title=None, ad_body=None):
    if not TAGS_CONFIG:
        return "Chia sẻ"
    overrides = TAGS_CONFIG.get("overrides", {})
    if cid in overrides:
        return ", ".join(overrides[cid])
    
    # Lấy thông điệp và nội dung hook
    hook_parts = [cname, adname]
    
    title = ad_title
    body = ad_body
    if adid and adid in AD_CREATIVES:
        cr = AD_CREATIVES[adid]
        title = title or cr.get("title", "")
        body = body or cr.get("body", "")
        
    if title:
        hook_parts.append(title)
    if body:
        lines = [l.strip() for l in body.split("\n") if l.strip()]
        hook_parts.append(" ".join(lines[:3])[:250])
        
    combined_hook = " | ".join(hook_parts).lower()
    cname_lower = cname.lower()
    
    scores = {
        "storytelling": 0,
        "PAS - problem - Agitation - solution": 0,
        "Tính năng - lợi ích ( đầu ra)": 0,
        "Lộ trình khóa học": 0,
        "Ưu đãi khuyến mãi": 0,
        "USP khóa học": 0,
        "Chia sẻ": 0
    }
    
    rules = TAGS_CONFIG.get("rules", {})
    
    # 1. Trọng số cao từ tên chiến dịch (weight: 10)
    for tag, conf in rules.items():
        c_pats = conf.get("campaign_patterns", [])
        for pat in c_pats:
            if re.search(pat, cname_lower, re.IGNORECASE):
                scores[tag] += 10
                break
                
    # 2. Trọng số từ nội dung hook quảng cáo (weight: 5)
    for tag, conf in rules.items():
        h_pats = conf.get("hook_patterns", [])
        for pat in h_pats:
            if re.search(pat, combined_hook, re.IGNORECASE):
                scores[tag] += 5
                break
                
    max_score = max(scores.values())
    if max_score == 0:
        return TAGS_CONFIG.get("default_tag", "Chia sẻ")
        
    chosen = [t for t, sc in scores.items() if sc >= max(4, max_score * 0.6)]
    chosen.sort(key=lambda t: scores[t], reverse=True)
    return ", ".join(chosen[:2])

# ─── PHÂN LOẠI SẢN PHẨM DỰA VÀO TÊN CHIẾN DỊCH & TÀI KHOẢN ──────────────────
def get_campaign_product(cname, aname=""):
    t = (cname or '').strip()
    a = (aname or '').strip().lower()
    tl = t.lower()
    
    # 1. Check strong prefixes/patterns in campaign name
    # XueBa (Tiếng Trung)
    if re.search(r'xueba|tiếng\s*trung|thầy\s*tư', tl):
        return 'XueBa'
    
    # Cyber Security
    if re.search(r'\b(cyber|cbs)\b', tl):
        return 'Network Security'
    
    # BrSE / Tsubasa / Japanese (Mặc định Tsu và BrSE là 1)
    if re.search(r'brse|tsu|tsubasa|tiếng\s*nhật|line\s*nhật', tl):
        return 'BrSE'
        
    # Embedded / Nhúng
    if re.search(r'nhúng|nhung|\b(embed|eb)\b', tl):
        return 'Embeded'
        
    # Data Engineer: check for - DE - or DE at start/key position
    if re.search(r'[-\s]de[-\s]|^\s*de[-\s]|\bdata\s*engin', tl):
        return 'Data Engineer'
        
    # Data Analyst: check for - DA - or DA at start/key position
    if re.search(r'[-\s]da[-\s]|^\s*da[-\s]|\bdata\s*analy', tl):
        return 'Data Analyst'
        
    # Business Analysis: check for - BA - or BA at start
    if re.search(r'[-\s]ba[-\s]|^\s*ba[-\s]|\bitba\b|business\s*analy', tl):
        return 'BA'
        
    # RA8 - AI NEW: các chiến dịch có tên là AI -> AI driven
    if ('ra8' in a or 'ai new' in a) and re.search(r'[-\s]ai[-\s]|^\s*ai[-\s]|\bai\b', tl):
        return 'AI driven'

    # AE, AIEG -> AI engineer
    if re.search(r'[-\s]ae[-\s]|^\s*ae[-\s]|\baieg\b|\bai4life\b', tl):
        return 'AI engineer'
        
    # PTIT / Đại học
    if re.search(r'ptit|cntt|qtkd', tl):
        return 'PTIT'
        
    # 2. Account fallback
    if 'dabk' in a: return 'Data Analyst'
    if ' - de' in a or 'ra3' in a: return 'Data Engineer'
    if ' - ba' in a or 'ra4' in a: return 'BA'
    if 'ai engineer' in a or 'ra2' in a: return 'AI engineer'
    if 'ai new' in a or 'ra8' in a: return 'AI driven'
    if 'embedded' in a or 'ra1' in a: return 'Embeded'
    if 'line nhật' in a or 'ra5' in a: return 'BrSE'
    if 'ptit' in a: return 'PTIT'
    
    return 'Khác'

def make_date_chunks(s_date, u_date, chunk_days=15):
    s_dt = datetime.strptime(s_date, "%Y-%m-%d")
    u_dt = datetime.strptime(u_date, "%Y-%m-%d")
    chunks = []
    curr = s_dt
    while curr <= u_dt:
        nxt = min(curr + timedelta(days=chunk_days - 1), u_dt)
        chunks.append((curr.strftime("%Y-%m-%d"), nxt.strftime("%Y-%m-%d")))
        curr = nxt + timedelta(days=1)
    return chunks

# ─── Helper: HTTP GET & POST ──────────────────────────────────────────────────
def http_get_json(url, retries=2, timeout=30):
    req = urllib.request.Request(url)
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except Exception as e:
            if attempt < retries:
                time.sleep(1)
            else:
                return None

def http_post_json(url, data_bytes=b'', retries=2, timeout=30):
    req = urllib.request.Request(url, data=data_bytes, method='POST')
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except Exception as e:
            if attempt < retries:
                time.sleep(1)
            else:
                return None

# ─── BƯỚC 1: LẤY DANH SÁCH FANPAGE TỪ PANCAKE ────────────────────────────────
print("=== 1. LẤY DANH SÁCH FANPAGE TỪ PANCAKE ===")
pages_url = f"{PANCAKE_USER_BASE}/pages?access_token={PANCAKE_TOKEN}"
pages_resp = http_get_json(pages_url)

pancake_pages = []
if pages_resp and isinstance(pages_resp, dict):
    pancake_pages = pages_resp.get("categorized", {}).get("activated", [])

if not pancake_pages:
    print("-> Không lấy được danh sách page từ Pancake User API, fallback qua Facebook Graph API...")
    url_fb_pages = f"https://graph.facebook.com/v19.0/me/accounts?fields=id,name&limit=100&access_token={FB_TOKEN}"
    fb_pages_data = http_get_json(url_fb_pages)
    if fb_pages_data and fb_pages_data.get("data"):
        pancake_pages = [{"id": p["id"], "name": p["name"]} for p in fb_pages_data["data"]]

if not pancake_pages:
    sys.exit("❌ Lỗi kết nối mạng hoặc Token: Không lấy được danh sách Fanpage từ Pancake và Facebook API.")

print(f"-> Tìm thấy {len(pancake_pages)} trang Fanpage đang kích hoạt.")

# ─── BƯỚC 2: TẠO PAGE ACCESS TOKEN & LẤY TAGS CHO TỪNG PAGE ─────────────────
print("\n=== 2. TẠO PAGE ACCESS TOKEN & LẤY DANH SÁCH TAGS PANCAKE ===")
page_tokens = {}  # pid -> page_access_token
tag_map = {}      # pid -> {tag_id: tag_name}

for p in pancake_pages:
    pid = str(p["id"])
    pname = p.get("name", pid)
    
    # 2.1 Tạo/Lấy Page Access Token
    gen_url = f"{PANCAKE_USER_BASE}/pages/{pid}/generate_page_access_token?page_id={pid}&access_token={PANCAKE_TOKEN}"
    token_resp = http_post_json(gen_url)
    if token_resp and token_resp.get("page_access_token"):
        page_tokens[pid] = token_resp["page_access_token"]
    else:
        continue

    # 2.2 Lấy danh sách thẻ (Tags)
    pat = page_tokens[pid]
    tags_url = f"{PANCAKE_PAGE_BASE}/pages/{pid}/tags?page_access_token={pat}"
    tags_resp = http_get_json(tags_url)
    tag_map[pid] = {}
    if tags_resp and isinstance(tags_resp, dict):
        for t in tags_resp.get("tags", []):
            tid = str(t.get("id", ""))
            tname = t.get("text") or t.get("name") or ""
            if tid and tname:
                tag_map[pid][tid] = tname
    
    print(f"  Trang: {pname[:35]} ({pid}) -> {len(tag_map[pid])} tags")
    time.sleep(0.15)

print(f"-> Đã tạo kết nối cho {len(page_tokens)} trang Pancake.")

# ─── BƯỚC 3: QUÉT HỘI THOẠI TỪ QUẢNG CÁO & BÓC TÁCH SĐT ─────────────────────
print(f"\n=== 3. QUÉT HỘI THOẠI TỪ ADS QUA PANCAKE ({SINCE_DATE} -> {UNTIL_DATE}) ===")

# ad_phones_by_date: {ad_id -> {date_str -> set(phones)}}
ad_phones_by_date = {}
# ad_tags_by_date: {ad_id -> {date_str -> set(tag_names)}}
ad_tags_by_date = {}

total_convs = 0
total_leads = 0

for pid, pat in page_tokens.items():
    page_name = next((p.get("name", pid) for p in pancake_pages if str(p["id"]) == pid), pid)
    page_tag_map = tag_map.get(pid, {})
    
    offset = 0
    page_conv_count = 0
    page_lead_count = 0
    page_conv_items = {}

    while True:
        exp_url = (
            f"{PANCAKE_PAGE_BASE}/pages/{pid}/export_data"
            f"?page_access_token={pat}&action=conversations_from_ads"
            f"&since={since_ts}&until={until_ts}&offset={offset}"
        )
        exp_data = http_get_json(exp_url, timeout=25)
        if not exp_data or not isinstance(exp_data, dict):
            break

        items = exp_data.get("data", [])
        if not items:
            break

        for item in items:
            conv_id = str(item.get("id", ""))
            if conv_id:
                page_conv_items.setdefault(conv_id, []).append(item)

        total_convs += len(items)
        if len(items) < 60:
            break
        offset += 60
        time.sleep(0.2)

    # Xử lý từng cuộc trò chuyện sau khi đã có toàn bộ các lượt tương tác
    for conv_id, it_list in page_conv_items.items():
        page_conv_count += 1
        items_with_phone = [x for x in it_list if x.get("recent_phone_numbers") and x.get("ad_clicks")]
        if not items_with_phone:
            continue

        # Lấy lượt tương tác mới nhất (gần nhất với thời điểm phát sinh/chốt SĐT)
        items_with_phone.sort(key=lambda x: x.get("inserted_at", ""))
        best_item = items_with_phone[-1]

        ad_clicks = best_item.get("ad_clicks", [])
        if not ad_clicks:
            continue
        ad_id = str(ad_clicks[0]).strip()
        if not ad_id:
            continue

        first_p = best_item["recent_phone_numbers"][0]
        phone = first_p.get("phone_number") if isinstance(first_p, dict) else str(first_p)
        if not phone:
            continue

        # Thời điểm phát sinh tương tác SĐT (Pancake export_data đã ở GMT+7)
        ins_time = best_item.get("inserted_at", "")
        date_str = ins_time[:10] if ins_time else UNTIL_DATE

        # Tổng hợp tags của cuộc trò chuyện
        conv_tag_names = set()
        for x in it_list:
            for tid in x.get("tags", []):
                t_str = str(tid)
                if t_str in page_tag_map:
                    conv_tag_names.add(page_tag_map[t_str])

        ad_phones_by_date.setdefault(ad_id, {}).setdefault(date_str, set()).add(phone)
        if conv_tag_names:
            ad_tags_by_date.setdefault(ad_id, {}).setdefault(date_str, set()).update(conv_tag_names)
        page_lead_count += 1
        total_leads += 1

    if page_lead_count > 0:
        print(f"  ✓ {page_name[:35]}: {page_conv_count} hội thoại ads, bóc tách {page_lead_count} SĐT.")

print(f"\n-> TỔNG KẾT PANCAKE: {total_convs} hội thoại từ ads, {total_leads} SĐT (Leads) gán cho {len(ad_phones_by_date)} Ad IDs.")

# ─── BƯỚC 4: THU THẬP INSIGHTS CẤP AD TỪ FACEBOOK GRAPH API ──────────────────
print("\n=== 4. THU THẬP METADATA & INSIGHTS CẤP AD TỪ 10 TÀI KHOẢN ADS ===")
url_accs = f"https://graph.facebook.com/v19.0/me/adaccounts?fields=id,name,currency,account_status&access_token={FB_TOKEN}"
accs_resp = http_get_json(url_accs)
accs = accs_resp.get('data', []) if accs_resp else []

time_range = json.dumps({'since': SINCE_DATE, 'until': UNTIL_DATE})
encoded_tr = urllib.parse.quote(time_range)

all_rows = []

for acc in accs:
    aid = acc['id']
    aname = acc['name']

    print(f"\n--- Đang xử lý tài khoản: {aname} ({aid}) ---")

    # Lấy campaigns
    url_camps = f"https://graph.facebook.com/v19.0/{aid}/campaigns?fields=id,name,status,effective_status,daily_budget,lifetime_budget,updated_time&limit=200&access_token={FB_TOKEN}"
    camps_data = http_get_json(url_camps)
    camps_map = {}
    if camps_data and 'data' in camps_data:
        for c in camps_data['data']:
            camps_map[c['id']] = c

    # Lấy ads
    url_ads = f"https://graph.facebook.com/v19.0/{aid}/ads?fields=id,name,status,effective_status,updated_time,campaign_id,creative{{id,name,effective_object_story_id,thumbnail_url,body,title,object_story_spec}}&limit=300&access_token={FB_TOKEN}"
    ads_data = http_get_json(url_ads)
    ads_map = {}
    if ads_data and 'data' in ads_data:
        for a in ads_data['data']:
            ads_map[a['id']] = a
            cr = a.get('creative', {})
            b_text = cr.get('body') or cr.get('object_story_spec', {}).get('link_data', {}).get('message', '') or ''
            t_text = cr.get('title') or cr.get('object_story_spec', {}).get('link_data', {}).get('name', '') or ''
            if b_text or t_text:
                AD_CREATIVES[a['id']] = {'title': t_text, 'body': b_text}

    # Lấy insights cấp Ad theo ngày (có phân trang và tự động chia chặng nếu Facebook timeout)
    fields = "date_start,campaign_id,campaign_name,ad_id,ad_name,spend,impressions,inline_link_clicks,ctr,cpc,cpm,actions"
    records = []
    
    # 1. Thử lấy toàn kỳ với pagination
    url_ins = f"https://graph.facebook.com/v19.0/{aid}/insights?level=ad&time_range={encoded_tr}&time_increment=1&fields={fields}&limit=250&access_token={FB_TOKEN}"
    curr_url = url_ins
    p = 0
    try:
        while curr_url and p < 30:
            ins_data = http_get_json(curr_url, retries=1, timeout=35)
            if not ins_data or 'data' not in ins_data:
                break
            batch = ins_data.get('data', [])
            records.extend(batch)
            curr_url = ins_data.get('paging', {}).get('next')
            p += 1
    except Exception as e:
        print(f"  ⚠️ Lỗi query toàn kỳ ({e}), chuyển sang query theo từng chặng 15 ngày...")

    # 2. Nếu thất bại hoặc không lấy được bản ghi (do Facebook timeout/500/400 như ở RA8)
    if len(records) == 0:
        print("  -> Đang query chia chặng 15 ngày để vượt giới hạn Facebook API...")
        chunks = make_date_chunks(SINCE_DATE, UNTIL_DATE, chunk_days=15)
        for since_d, until_d in chunks:
            tr = json.dumps({'since': since_d, 'until': until_d})
            etr = urllib.parse.quote(tr)
            chunk_url = f"https://graph.facebook.com/v19.0/{aid}/insights?level=ad&time_range={etr}&time_increment=1&fields={fields}&limit=200&access_token={FB_TOKEN}"
            curr_url = chunk_url
            cp = 0
            while curr_url and cp < 20:
                cdata = http_get_json(curr_url, retries=1, timeout=35)
                if not cdata or 'data' not in cdata:
                    break
                records.extend(cdata.get('data', []))
                curr_url = cdata.get('paging', {}).get('next')
                cp += 1

    print(f"  Số bản ghi chi tiết (ngày x ad): {len(records)}")

    for r in records:
        date_str = r.get('date_start', '')
        cid = r.get('campaign_id', '')
        cname = r.get('campaign_name', '')
        adid = r.get('ad_id', '')
        adname = r.get('ad_name', '')

        c_obj = camps_map.get(cid, {})
        ad_obj = ads_map.get(adid, {})

        status = ad_obj.get('effective_status') or c_obj.get('effective_status') or 'UNKNOWN'

        daily_b = c_obj.get('daily_budget')
        daily_budget_str = f"{float(daily_b):,.0f}" if daily_b else "CBO/Nhóm"

        spend = float(r.get('spend', 0))
        impressions = int(r.get('impressions', 0))
        clicks = int(r.get('inline_link_clicks', 0))
        ctr = float(r.get('ctr', 0))
        cpc = float(r.get('cpc', 0)) if r.get('cpc') else (spend / clicks if clicks > 0 else 0)
        cpm = float(r.get('cpm', 0))

        actions = r.get('actions', [])
        messages = 0
        leads = 0
        registrations = 0

        for act in actions:
            atype = act.get('action_type', '')
            val = int(act.get('value', 0))
            if atype in ['onsite_conversion.messaging_conversation_started_7d', 'onsite_conversion.messaging_first_reply']:
                if val > messages:
                    messages = val
            elif atype in ['lead', 'onsite_conversion.lead_grouped', 'onsite_web_lead', 'onsite_conversion.lead']:
                if val > leads:
                    leads = val
            elif atype in ['complete_registration', 'offsite_complete_registration_add_meta_leads']:
                if val > registrations:
                    registrations = val

        total_conv = messages + leads + registrations
        cpa = (spend / total_conv) if total_conv > 0 else 0

        updated_time = ad_obj.get('updated_time') or c_obj.get('updated_time') or ''

        # ─── Số SĐT từ PANCAKE theo (ad_id, ngày) ───────────────────────────
        sdt_count = 0
        if adid in ad_phones_by_date and date_str in ad_phones_by_date[adid]:
            sdt_count = len(ad_phones_by_date[adid][date_str])

        # Tags Pancake tổng hợp cho (ad_id, ngày)
        tags_str = ""
        if adid in ad_tags_by_date and date_str in ad_tags_by_date[adid]:
            tags_str = ", ".join(sorted(ad_tags_by_date[adid][date_str]))

        # Link bài viết quảng cáo Facebook
        c_creative = ad_obj.get('creative', {})
        story_id = c_creative.get('effective_object_story_id')
        if story_id:
            ad_link = f"https://www.facebook.com/{story_id}"
        else:
            ad_link = f"https://adsmanager.facebook.com/adsmanager/manage/ads?act={aid.replace('act_', '')}&selected_ad_ids={adid}"

        c_body = c_creative.get('body') or c_creative.get('object_story_spec', {}).get('link_data', {}).get('message', '')
        c_title = c_creative.get('title') or c_creative.get('object_story_spec', {}).get('link_data', {}).get('name', '')
        camp_tags = get_campaign_tags(cid, cname, adname, aname, adid=adid, ad_title=c_title, ad_body=c_body)
        camp_prod = get_campaign_product(cname, aname)

        all_rows.append({
            "Tài khoản": aname,
            "ID tài khoản": aid,
            "Ngày": date_str,
            "Campaign ID": cid,
            "Tên chiến dịch": cname,
            "Sản phẩm": camp_prod,
            "Trạng thái": status,
            "Ngân sách/ngày": daily_budget_str,
            "Chi tiêu": round(spend, 0),
            "Hiển thị": impressions,
            "Click link": clicks,
            "CTR (%)": round(ctr, 2),
            "CPC": round(cpc, 0),
            "CPM": round(cpm, 0),
            "Tin nhắn": messages,
            "Lead": leads,
            "Đăng ký": registrations,
            "CPA": round(cpa, 0),
            "Cập nhật lúc": updated_time,
            "ID quảng cáo": adid,
            "Tên quảng cáo": adname,
            "Sđt theo campain": sdt_count,
            "Tags Pancake": tags_str,
            "Nhãn chiến dịch": camp_tags,
            "Link bài quảng cáo": ad_link,
        })

print(f"\n-> Tổng số dòng dữ liệu tổng hợp: {len(all_rows)}")

if len(all_rows) == 0:
    print("❌ LỖI: Không thu thập được bản ghi nào từ Facebook API! Hủy ghi đè để bảo vệ dữ liệu cũ.")
    sys.exit(1)

# ─── BƯỚC 5: GỘP DỮ LIỆU CŨ & MỚI (BẢO TOÀN LỊCH SỬ) VÀ XUẤT CSV ──────────────
print("\n=== 5. GỘP DỮ LIỆU CŨ & MỚI (BẢO TOÀN LỊCH SỬ) ===")
csv_file = CSV_FILE

merged_map = {}
old_kept_count = 0

# 1. Nạp các bản ghi cũ trước ngày SINCE_DATE
for r in existing_rows:
    d = r.get("Ngày", "").strip()
    if d and d < SINCE_DATE:
        k = (r.get("ID tài khoản", "").strip(), d, r.get("Campaign ID", "").strip(), r.get("ID quảng cáo", "").strip())
        merged_map[k] = r
        old_kept_count += 1

# 2. Nạp các bản ghi mới vừa thu thập (ghi đè hoặc thêm mới cho các ngày >= SINCE_DATE)
new_added_count = 0
for r in all_rows:
    d = r.get("Ngày", "").strip()
    k = (r.get("ID tài khoản", "").strip(), d, r.get("Campaign ID", "").strip(), r.get("ID quảng cáo", "").strip())
    merged_map[k] = r
    new_added_count += 1

final_rows = list(merged_map.values())

# Sắp xếp theo thứ tự: Ngày giảm dần, Tài khoản, Tên chiến dịch, ID quảng cáo
final_rows.sort(key=lambda r: (
    r.get("Ngày", ""),
    r.get("Tài khoản", ""),
    r.get("Tên chiến dịch", ""),
    r.get("ID quảng cáo", "")
), reverse=True)

print(f"  - Số bản ghi lịch sử cũ được bảo toàn (< {SINCE_DATE}): {old_kept_count}")
print(f"  - Số bản ghi mới / làm mới vừa thu thập (>= {SINCE_DATE}): {new_added_count}")
print(f"  -> Tổng số dòng dữ liệu hoàn chỉnh sau khi gộp: {len(final_rows)}")

fieldnames = [
    "Tài khoản", "ID tài khoản", "Ngày", "Campaign ID", "Tên chiến dịch", "Sản phẩm", "Trạng thái",
    "Ngân sách/ngày", "Chi tiêu", "Hiển thị", "Click link", "CTR (%)", "CPC", "CPM",
    "Tin nhắn", "Lead", "Đăng ký", "CPA", "Cập nhật lúc", "ID quảng cáo", "Tên quảng cáo",
    "Sđt theo campain", "Tags Pancake", "Nhãn chiến dịch", "Link bài quảng cáo"
]

with open(csv_file, 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for row in final_rows:
        writer.writerow(row)

print(f"✓ Đã xuất file CSV thành công: {csv_file}")

# ─── BƯỚC 6: XUẤT BÁO CÁO MARKDOWN TỔNG HỢP ──────────────────────────────────
md_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Bao_Cao_FB", "Bao_Cao_Tong_Hop_Cac_Tai_Khoan_10_2026.md")

min_date_all = min((r.get("Ngày") for r in final_rows if r.get("Ngày")), default=SINCE_DATE)
max_date_all = max((r.get("Ngày") for r in final_rows if r.get("Ngày")), default=UNTIL_DATE)
total_sdt_all = sum(int(float(r.get("Sđt theo campain", 0) or 0)) for r in final_rows)
unique_ads_all = len(set(r.get("ID quảng cáo") for r in final_rows if r.get("ID quảng cáo")))

with open(md_file, 'w', encoding='utf-8') as f:
    f.write(f"# 📊 BÁO CÁO HIỆU QUẢ QUẢNG CÁO THEO TÀI KHOẢN ({min_date_all} - HIỆN TẠI)\n\n")
    f.write(f"> **Thời gian ghi nhận:** {min_date_all} – {max_date_all}\n")
    f.write(f"> **Nguồn dữ liệu:** Facebook Graph API v19.0 (Insights) + **Pancake API** (SĐT bóc tách từ hội thoại quảng cáo, Tags).\n")
    f.write(f"> **Tổng SĐT bóc tách từ Pancake gắn Ads:** {total_sdt_all} leads từ {unique_ads_all} Ad IDs\n")
    f.write(f"> **Đợt cập nhật gần nhất:** {datetime.now(VN_TZ).strftime('%d/%m/%Y %H:%M:%S')} (Chế độ: {SINCE_DATE} -> {UNTIL_DATE})\n")
    f.write(f"> **File CSV chi tiết:** [`data/bao_cao_cac_tai_khoan_10_2026.csv`](file:///d:/MCP/data/bao_cao_cac_tai_khoan_10_2026.csv)\n\n")

    f.write("## 🏆 1. BẢNG TỔNG HỢP HIỆU SUẤT THEO TÀI KHOẢN\n\n")
    f.write("| Tài khoản | Chi tiêu (VNĐ) | Hiển thị | Clicks | CTR TB | CPC TB | Tin nhắn | SĐT (Pancake) | CPA TB (VNĐ) |\n")
    f.write("|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|\n")

    acc_summary = {}
    for r in final_rows:
        acc_name = r["Tài khoản"]
        s = acc_summary.setdefault(acc_name, {"spend": 0.0, "imp": 0, "clicks": 0, "msg": 0, "sdt": 0, "reg": 0})
        s["spend"] += float(r.get("Chi tiêu", 0) or 0)
        s["imp"] += int(float(r.get("Hiển thị", 0) or 0))
        s["clicks"] += int(float(r.get("Click link", 0) or 0))
        s["msg"] += int(float(r.get("Tin nhắn", 0) or 0))
        s["sdt"] += int(float(r.get("Sđt theo campain", 0) or 0))
        s["reg"] += int(float(r.get("Đăng ký", 0) or 0))

    for aname, s in sorted(acc_summary.items(), key=lambda x: x[1]["spend"], reverse=True):
        ctr_v = (s["clicks"] / s["imp"] * 100) if s["imp"] > 0 else 0
        cpc_v = (s["spend"] / s["clicks"]) if s["clicks"] > 0 else 0
        conv_v = s["msg"] + s["sdt"] + s["reg"]
        cpa_v = (s["spend"] / conv_v) if conv_v > 0 else 0
        f.write(f"| **{aname}** | {s['spend']:,.0f} | {s['imp']:,.0f} | {s['clicks']:,.0f} | {ctr_v:.2f}% | {cpc_v:,.0f} | {s['msg']:,} | **{s['sdt']:,}** | {cpa_v:,.0f} |\n")

    # Bảng tổng hợp theo Sản phẩm
    f.write("\n---\n")
    f.write("## 📦 2. BẢNG TỔNG HỢP HIỆU SUẤT THEO SẢN PHẨM\n\n")
    f.write("| Sản phẩm | Chi tiêu (VNĐ) | Hiển thị | Clicks | CTR TB | Tin nhắn | SĐT (Pancake) | Chi phí / SĐT (VNĐ) |\n")
    f.write("|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|\n")
    prod_summary = {}
    for r in final_rows:
        pname = r.get("Sản phẩm") or "Khác"
        s = prod_summary.setdefault(pname, {"spend": 0.0, "imp": 0, "clicks": 0, "msg": 0, "sdt": 0})
        s["spend"] += float(r.get("Chi tiêu", 0) or 0)
        s["imp"] += int(float(r.get("Hiển thị", 0) or 0))
        s["clicks"] += int(float(r.get("Click link", 0) or 0))
        s["msg"] += int(float(r.get("Tin nhắn", 0) or 0))
        s["sdt"] += int(float(r.get("Sđt theo campain", 0) or 0))

    for pname, s in sorted(prod_summary.items(), key=lambda x: x[1]["sdt"], reverse=True):
        ctr_v = (s["clicks"] / s["imp"] * 100) if s["imp"] > 0 else 0
        cost_per_sdt = (s["spend"] / s["sdt"]) if s["sdt"] > 0 else 0
        f.write(f"| **{pname}** | {s['spend']:,.0f} | {s['imp']:,.0f} | {s['clicks']:,.0f} | {ctr_v:.2f}% | {s['msg']:,} | **{s['sdt']:,}** | {cost_per_sdt:,.0f} |\n")

    # Bảng tổng hợp theo Nhãn chiến dịch / Nhóm nội dung
    f.write("\n---\n")
    f.write("## 🏷️ 3. BẢNG TỔNG HỢP HIỆU SUẤT THEO NHÓM NỘI DUNG (NHÃN CHIẾN DỊCH)\n\n")
    f.write("| Nhóm nội dung / Tag | Chi tiêu (VNĐ) | Tin nhắn | SĐT (Pancake) | Chi phí / SĐT (VNĐ) |\n")
    f.write("|---|:---:|:---:|:---:|:---:|\n")
    tag_summary = {}
    for r in final_rows:
        raw_tags = r.get("Nhãn chiến dịch", "")
        t_list = [t.strip() for t in raw_tags.split(",") if t.strip()]
        if not t_list:
            t_list = ["Chưa phân loại"]
        for t in t_list:
            s = tag_summary.setdefault(t, {"spend": 0.0, "msg": 0, "sdt": 0})
            s["spend"] += float(r.get("Chi tiêu", 0) or 0)
            s["msg"] += int(float(r.get("Tin nhắn", 0) or 0))
            s["sdt"] += int(float(r.get("Sđt theo campain", 0) or 0))

    for tname, s in sorted(tag_summary.items(), key=lambda x: x[1]["sdt"], reverse=True):
        cost_per_sdt = (s["spend"] / s["sdt"]) if s["sdt"] > 0 else 0
        f.write(f"| **{tname}** | {s['spend']:,.0f} | {s['msg']:,} | **{s['sdt']:,}** | {cost_per_sdt:,.0f} |\n")

    f.write("\n---\n")
    f.write("## 📑 4. CHI TIẾT DỮ LIỆU CÁC CHIẾN DỊCH THEO TỪNG TÀI KHOẢN\n\n")

    for aname in acc_summary.keys():
        rows_acc = [r for r in final_rows if r["Tài khoản"] == aname]
        f.write(f"### 🏢 {aname} ({len(rows_acc)} dòng)\n\n")
        f.write("| Ngày | Chiến dịch | Sản phẩm | Tag chiến dịch | Trạng thái | Chi tiêu | Tin nhắn | Lead | **SĐT** | Tags Pancake | ID quảng cáo |\n")
        f.write("|:---:|---|:---:|---|:---:|:---:|:---:|:---:|:---:|---|:---:|\n")
        for r in rows_acc[:20]:
            tags_display = r.get('Tags Pancake', '')[:30] + '…' if len(r.get('Tags Pancake', '')) > 30 else r.get('Tags Pancake', '')
            camp_tag_display = r.get('Nhãn chiến dịch', '')
            spend_val = float(r.get("Chi tiêu", 0) or 0)
            f.write(f"| {r['Ngày']} | {r['Tên chiến dịch'][:32]} | **{r.get('Sản phẩm', '')}** | {camp_tag_display} | {r['Trạng thái']} | {spend_val:,.0f} | {r['Tin nhắn']} | {r['Lead']} | **{r['Sđt theo campain']}** | {tags_display} | `{r['ID quảng cáo']}` |\n")
        if len(rows_acc) > 20:
            f.write(f"\n*(Còn {len(rows_acc) - 20} dòng khác, xem trong file CSV)*\n\n")
        f.write("\n")

print(f"Đã xuất báo cáo Markdown thành công: {md_file}")
