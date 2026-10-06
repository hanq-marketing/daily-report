import os
import json
import urllib.request
import urllib.error
import datetime

# Lấy token từ biến môi trường
FB_TOKEN = os.environ.get('FB_TOKEN')

if not FB_TOKEN:
    try:
        with open('.env', 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('FB_TOKEN='):
                    FB_TOKEN = line.strip().split('=', 1)[1]
    except Exception:
        pass

if not FB_TOKEN:
    print("Error: FB_TOKEN is missing!")
    exit(1)

def fetch_json(url):
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.URLError as e:
        print(f"Failed to fetch {url}: {e}")
        return None

def fetch_data_for_preset(accounts_list, base_url, date_preset):
    mapped_accounts = []
    total_spend = 0
    total_convs = 0
    
    for acc in accounts_list:
        camp_url = f"{base_url}/{acc['id']}/campaigns?fields=id,name,status,effective_status,daily_budget,ads.limit(10){{id,name,status,creative{{effective_object_story_id,thumbnail_url}}}},adsets.limit(1){{targeting}},insights.date_preset({date_preset}){{spend,impressions,inline_link_clicks,inline_link_click_ctr,cpc,cpm,actions}}&limit=100&access_token={FB_TOKEN}"
        camp_data = fetch_json(camp_url)
        if not camp_data or 'data' not in camp_data:
            continue
            
        campaigns = camp_data['data']
        acc_spend = 0
        mapped_campaigns = []
        
        for c in campaigns:
            insights_data = c.get('insights', {}).get('data', [])
            if not insights_data:
                continue
                
            ins = insights_data[0]
            convs = 0
            actions = ins.get('actions', [])
            for act in actions:
                if act.get('action_type') in ['onsite_conversion.messaging_conversation_started_7d', 'lead', 'complete_registration', 'purchase', 'messaging_conversation_started_7d', 'onsite_conversion.messaging_conversation_started_28d']:
                    convs += int(act.get('value', 0))
            
            spend = float(ins.get('spend', 0))
            cpm = float(ins.get('cpm', 0))
            cpc = float(ins.get('cpc', 0))
            ctr = float(ins.get('inline_link_click_ctr', 0))
            cpa = (spend / convs) if convs > 0 else 0
            
            acc_spend += spend
            total_spend += spend
            total_convs += convs
            
            rating = "Stable"
            if spend > 0 and convs == 0:
                rating = "RED"
            elif cpa > 150000:
                rating = "ORANGE"
            elif cpa > 0 and cpa <= 100000:
                rating = "GREEN"

            mapped_ads = []
            ads_data = c.get('ads', {}).get('data', [])
            for ad in ads_data:
                creative = ad.get('creative', {})
                post_id = creative.get('effective_object_story_id', '')
                thumb_url = creative.get('thumbnail_url', '')
                mapped_ads.append({
                    "id": ad.get('id', ''),
                    "name": ad.get('name', ''),
                    "status": ad.get('status', ''),
                    "postId": post_id,
                    "thumbnail": thumb_url
                })
                
            targeting_summary = "Không rõ"
            adsets_data = c.get('adsets', {}).get('data', [])
            if adsets_data and len(adsets_data) > 0:
                t_obj = adsets_data[0].get('targeting', {})
                age = f"{t_obj.get('age_min', '18')}-{t_obj.get('age_max', '65+')}"
                geo = "Việt Nam"
                geo_obj = t_obj.get('geo_locations', {})
                if 'countries' in geo_obj:
                    geo = ", ".join(geo_obj['countries'])
                elif 'custom_locations' in geo_obj:
                    geo = "Nhiều khu vực (VN)"
                    
                platforms = ", ".join(t_obj.get('publisher_platforms', ['Tự động']))
                
                interests = []
                flex = t_obj.get('flexible_spec', [])
                for f in flex:
                    if 'interests' in f:
                        for idx, interest in enumerate(f['interests']):
                            if idx < 3:
                                interests.append(interest.get('name', ''))
                
                targeting_summary = f"Độ tuổi: {age}<br>Vị trí: {geo}<br>Nền tảng: {platforms}"
                if interests:
                    targeting_summary += f"<br>Sở thích: {', '.join(interests)}..."
                
            mapped_campaigns.append({
                "id": c.get('id', ''),
                "name": c.get('name', ''),
                "status": c.get('status', ''),
                "effectiveStatus": c.get('effective_status', ''),
                "budget": c.get('daily_budget', '0'),
                "spendCurrent": spend,
                "spendPrior": 0,
                "spendChange": 0,
                "cpmCurrent": cpm,
                "cpmPrior": cpm,
                "cpmChange": 0,
                "cpcCurrent": cpc,
                "cpcPrior": cpc,
                "cpcChange": 0,
                "ctrCurrent": ctr,
                "ctrPrior": ctr,
                "ctrChange": 0,
                "cpaCurrent": cpa,
                "cpaPrior": cpa,
                "cpaChange": 0,
                "conversionsCurrent": convs,
                "conversionsPrior": 0,
                "conversionsChange": 0,
                "rating": rating,
                "ads": mapped_ads,
                "targetingSummary": targeting_summary,
                "hookRate": 0,
                "holdRate": 0
            })
            
        if mapped_campaigns:
            mapped_accounts.append({
                "id": acc.get('id', ''),
                "name": acc.get('name', ''),
                "status": "ACTIVE" if acc.get('account_status') == 1 else "DISABLED",
                "currency": acc.get('currency', 'VND'),
                "rating": "Stable" if acc_spend > 0 else "DISABLED",
                "evaluation": "",
                "recommendation": "",
                "campaigns": mapped_campaigns
            })
            
    return {
        "summary": {
            "scannedAccounts": len(accounts_list),
            "activeAccounts": len(mapped_accounts),
            "disabledAccounts": 0,
            "totalSpend": total_spend,
            "totalConversions": total_convs,
            "auditMode": f"API: {date_preset.upper()}"
        },
        "criticalAlerts": [],
        "priorityActions": [],
        "accounts": mapped_accounts
    }

def main():
    version = 'v17.0'
    base_url = f"https://graph.facebook.com/{version}"
    
    # Fetch accounts
    acc_url = f"{base_url}/me/adaccounts?fields=id,name,account_status,currency&limit=50&access_token={FB_TOKEN}"
    acc_data = fetch_json(acc_url)
    if not acc_data or 'data' not in acc_data:
        print("Error fetching accounts or no accounts found.")
        exit(1)
        
    accounts_list = acc_data['data']
    
    print("Fetching 'today'...")
    today_data = fetch_data_for_preset(accounts_list, base_url, 'today')
    
    print("Fetching 'yesterday'...")
    yesterday_data = fetch_data_for_preset(accounts_list, base_url, 'yesterday')
    
    print("Fetching 'last_7d'...")
    last7d_data = fetch_data_for_preset(accounts_list, base_url, 'last_7d')
    
    report_data = {
        "today": today_data,
        "yesterday": yesterday_data,
        "last7d": last7d_data,
        "lastUpdated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    os.makedirs('data', exist_ok=True)
    with open('data/reportData.json', 'w', encoding='utf-8') as f:
        json.dump(report_data, f, ensure_ascii=False, indent=4)
        
    print("Successfully fetched all data and wrote to data/reportData.json")

if __name__ == "__main__":
    main()
