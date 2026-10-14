import urllib.request
import csv
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1PD3zhqZ2rTZlMi7X3lsCh6fkvNcR-B2kGv0m9L0Fl_4/gviz/tq?tqx=out:csv&sheet=Master%20Data"

def main():
    print("=== [1] KÉO DỮ LIỆU TỪ GOOGLE SHEETS (MASTER DATA) ===")
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_file = os.path.join(base_dir, "data", "bao_cao_cac_tai_khoan_10_2026.csv")
    os.makedirs(os.path.dirname(csv_file), exist_ok=True)

    req = urllib.request.Request(SHEET_CSV_URL, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            content = resp.read().decode('utf-8')
    except Exception as e:
        print(f"❌ LỖI kết nối Google Sheets: {e}")
        sys.exit(1)

    if not content or len(content) < 100:
        print("❌ LỖI: Dữ liệu tải về từ Google Sheets rỗng hoặc không hợp lệ!")
        sys.exit(1)

    # Ghi đè vào data/bao_cao_cac_tai_khoan_10_2026.csv
    with open(csv_file, 'w', encoding='utf-8-sig', newline='') as f:
        f.write(content)

    print(f"✓ Đã lưu dữ liệu Google Sheet vào: {csv_file}")

    print("\n=== [2] BIÊN DỊCH & CẬP NHẬT DASHBOARD (index.html) ===")
    script_build = os.path.join(base_dir, "scripts", "build_dashboard.py")
    if os.path.exists(script_build):
        import subprocess
        res = subprocess.run([sys.executable, script_build], capture_output=False)
        if res.returncode != 0:
            print("❌ Lỗi khi build dashboard index.html!")
            sys.exit(res.returncode)
    else:
        print("⚠️ Không tìm thấy scripts/build_dashboard.py, bỏ qua bước build HTML.")

    print("\n✅ HOÀN TẤT ĐỒNG BỘ DỮ LIỆU TỪ GOOGLE SHEETS SANG DASHBOARD!")

if __name__ == "__main__":
    main()
