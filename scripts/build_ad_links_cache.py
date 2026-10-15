import urllib.request
import json
import os
import sys
import csv

sys.stdout.reconfigure(encoding='utf-8')
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(base_dir, '.env')
token = ""
with open(env_path, 'r', encoding='utf-8') as f:
    for line in f:
        if line.startswith('FB_TOKEN='):
            token = line.split('=', 1)[1].strip()

# Read unique ad_ids and account_ids from CSV
csv_path = os.path.join(base_dir, 'data', 'bao_cao_cac_tai_khoan_10_2026.csv')
acc_ads = {}
with open(csv_path, 'r', encoding='utf-8-sig') as f:
    for r in csv.DictReader(f):
        aid = r.get('ID tài khoản')
        adid = r.get('ID quảng cáo')
        if aid and adid:
            acc_ads.setdefault(aid, set()).add(adid)

print(f"Đang quét {len(acc_ads)} tài khoản Facebook Ads...")
ad_links = {}

for aid, adids in acc_ads.items():
    url = f"https://graph.facebook.com/v19.0/{aid}/ads?fields=id,name,creative{{id,name,effective_object_story_id,thumbnail_url}}&limit=300&access_token={token}"
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        for a in data.get('data', []):
            adid = a['id']
            if adid in adids:
                c = a.get('creative', {})
                story_id = c.get('effective_object_story_id')
                if story_id:
                    post_url = f"https://www.facebook.com/{story_id}"
                else:
                    post_url = f"https://adsmanager.facebook.com/adsmanager/manage/ads?act={aid.replace('act_', '')}&selected_ad_ids={adid}"
                ad_links[adid] = {
                    "url": post_url,
                    "story_id": story_id or "",
                    "thumb": c.get('thumbnail_url', ''),
                    "name": a.get('name', '')
                }
    except Exception as e:
        print(f"Lỗi tài khoản {aid}: {e}")

cache_file = os.path.join(base_dir, 'data', 'ad_links_cache.json')
with open(cache_file, 'w', encoding='utf-8') as f:
    json.dump(ad_links, f, ensure_ascii=False, indent=2)

print(f"✓ Đã lưu cache link bài quảng cáo vào: {cache_file} ({len(ad_links)} ads)")
