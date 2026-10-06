import os
import json
import urllib.request
import urllib.error
import urllib.parse
import datetime

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

def fetch_data(accounts_list, base_url, mode):
    mapped_accounts = []
    total_spend = 0
    total_convs = 0
    
    for acc in accounts_list:
        tz_offset = acc.get('timezone_offset_hours_utc', 7)
        acc_now = datetime.datetime.utcnow() + datetime.timedelta(hours=tz_offset)
        acc_today = acc_now.date()
        
        if mode == 'today':
            curr_start = acc_today
            curr_end = acc_today
            prior_start = acc_today - datetime.timedelta(days=3)
            prior_end = acc_today - datetime.timedelta(days=1)
            days_divisor = 3
        elif mode == 'yesterday':
            curr_start = acc_today - datetime.timedelta(days=1)
            curr_end = acc_today - datetime.timedelta(days=1)
            prior_start = acc_today - datetime.timedelta(days=4)
            prior_end = acc_today - datetime.timedelta(days=2)
            days_divisor = 3
        else: # last_7d
            curr_start = acc_today - datetime.timedelta(days=6)
            curr_end = acc_today
            prior_start = acc_today - datetime.timedelta(days=13)
            prior_end = acc_today - datetime.timedelta(days=7)
            days_divisor = 7
            
        ranges = f'[{{"since":"{curr_start}","until":"{curr_end}"}},{{"since":"{prior_start}","until":"{prior_end}"}}]'
        ranges_encoded = urllib.parse.quote(ranges)
        
        camp_url = f"{base_url}/{acc['id']}/campaigns?fields=id,name,status,effective_status,daily_budget,ads.limit(10){{id,name,status,creative{{effective_object_story_id,thumbnail_url}}}},adsets.limit(1){{targeting}},insights.time_ranges({ranges_encoded}){{spend,impressions,inline_link_clicks,inline_link_click_ctr,cpc,cpm,actions,date_start,date_stop}}&limit=100&access_token={FB_TOKEN}"
        
        camp_data = fetch_json(camp_url)
        if not camp_data or 'data' not in camp_data:
            continue
            
        campaigns = camp_data['data']
        acc_spend = 0
        mapped_campaigns = []
        
        for c in campaigns:
            insights_data = c.get('insights', {}).get('data', [])
            curr_ins = {}
            prior_ins = {}
            
            for ins in insights_data:
                if ins.get('date_start') == str(curr_start) and ins.get('date_stop') == str(curr_end):
                    curr_ins = ins
                elif ins.get('date_start') == str(prior_start) and ins.get('date_stop') == str(prior_end):
                    prior_ins = ins
            
            if not curr_ins:
                continue
                
            def extract_metrics(ins, div=1):
                spend_tot = float(ins.get('spend', 0))
                spend_avg = spend_tot / div
                cpm = float(ins.get('cpm', 0))
                ctr = float(ins.get('inline_link_click_ctr', 0))
                link_clicks = int(ins.get('inline_link_clicks', 0))
                cpc = (spend_tot / link_clicks) if link_clicks > 0 else 0
                convs_tot = 0
                for act in ins.get('actions', []):
                    if act.get('action_type') in ['onsite_conversion.messaging_conversation_started_7d', 'messaging_conversation_started_7d']:
                        convs_tot += int(act.get('value', 0))
                convs_avg = convs_tot / div
                cpa = (spend_tot / convs_tot) if convs_tot > 0 else 0
                return spend_avg, cpm, ctr, cpc, convs_avg, cpa
                
            spend_curr, cpm_curr, ctr_curr, cpc_curr, convs_curr, cpa_curr = extract_metrics(curr_ins, 1)
            spend_prior, cpm_prior, ctr_prior, cpc_prior, convs_prior, cpa_prior = extract_metrics(prior_ins, days_divisor) if prior_ins else (0,0,0,0,0,0)
            
            # Tính toán phần trăm thay đổi
            def safe_pct(curr, prior):
                if prior > 0:
                    return ((curr - prior) / prior) * 100
                return 0
                
            acc_spend += spend_curr
            total_spend += spend_curr
            total_convs += convs_curr
            
            rating = "Stable"
            if spend_curr > 0 and convs_curr == 0:
                rating = "RED"
            elif cpa_curr > 150000:
                rating = "ORANGE"
            elif cpa_curr > 0 and cpa_curr <= 100000:
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
                "spendCurrent": spend_curr,
                "spendPrior": spend_prior,
                "spendChange": safe_pct(spend_curr, spend_prior),
                "cpmCurrent": cpm_curr,
                "cpmPrior": cpm_prior,
                "cpmChange": safe_pct(cpm_curr, cpm_prior),
                "cpcCurrent": cpc_curr,
                "cpcPrior": cpc_prior,
                "cpcChange": safe_pct(cpc_curr, cpc_prior),
                "ctrCurrent": ctr_curr,
                "ctrPrior": ctr_prior,
                "ctrChange": safe_pct(ctr_curr, ctr_prior),
                "cpaCurrent": cpa_curr,
                "cpaPrior": cpa_prior,
                "cpaChange": safe_pct(cpa_curr, cpa_prior),
                "conversionsCurrent": convs_curr,
                "conversionsPrior": convs_prior,
                "conversionsChange": safe_pct(convs_curr, convs_prior),
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
            "auditMode": f"API: {mode.upper()}"
        },
        "criticalAlerts": [],
        "priorityActions": [],
        "accounts": mapped_accounts
    }

def main():
    version = 'v17.0'
    base_url = f"https://graph.facebook.com/{version}"
    
    # Fetch accounts
    acc_url = f"{base_url}/me/adaccounts?fields=id,name,account_status,currency,timezone_offset_hours_utc&limit=50&access_token={FB_TOKEN}"
    acc_data = fetch_json(acc_url)
    if not acc_data or 'data' not in acc_data:
        print("Error fetching accounts or no accounts found.")
        exit(1)
        
    accounts_list = acc_data['data']
    
    print("Fetching 'today'...")
    today_data = fetch_data(accounts_list, base_url, 'today')
    
    print("Fetching 'yesterday'...")
    yesterday_data = fetch_data(accounts_list, base_url, 'yesterday')
    
    print("Fetching 'last_7d'...")
    last7d_data = fetch_data(accounts_list, base_url, 'last_7d')
    
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
