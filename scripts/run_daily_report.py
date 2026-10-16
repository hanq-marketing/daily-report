import subprocess
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

def main():
    print("=================================================================")
    print("🚀 BẮT ĐẦU QUY TRÌNH CẬP NHẬT BÁO CÁO FACEBOOK ADS HÀNG NGÀY")
    print("=================================================================\n")

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    script_gen = os.path.join(base_dir, "scripts", "generate_multiacct_report.py")
    script_cache = os.path.join(base_dir, "scripts", "build_ad_links_cache.py")
    script_sync = os.path.join(base_dir, "scripts", "update_google_sheet.py")

    # Bước 1: Kéo dữ liệu từ Facebook Graph API và tạo CSV + Markdown
    print("👉 BƯỚC 1: Thu thập dữ liệu từ Facebook API & đối soát SĐT theo ID quảng cáo...")
    res1 = subprocess.run([sys.executable, script_gen], capture_output=False)
    if res1.returncode != 0:
        print("\n❌ LỖI: Bước 1 thất bại! Dừng quy trình.")
        sys.exit(res1.returncode)

    print("\n-----------------------------------------------------------------")
    # Bước 1.5: Cập nhật cache liên kết bài quảng cáo & thumbnails
    if os.path.exists(script_cache):
        print("👉 BƯỚC 1.5: Quét và cập nhật cache link bài quảng cáo & thumbnail...")
        subprocess.run([sys.executable, script_cache], capture_output=False)

    print("\n-----------------------------------------------------------------")
    # Bước 2: Đối soát và đồng bộ lũy kế lên Google Sheets
    print("👉 BƯỚC 2: Đối soát và đồng bộ lũy kế lên Google Sheets (giữ nguyên dữ liệu cũ)...")
    res2 = subprocess.run([sys.executable, script_sync], capture_output=False)
    if res2.returncode != 0:
        print("\n❌ LỖI: Bước 2 thất bại!")
    print("\n-----------------------------------------------------------------")
    # Bước 3: Cập nhật Dashboard trực quan hóa index.html
    print("👉 BƯỚC 3: Cập nhật Dashboard trực quan hóa (index.html)...")
    script_dash = os.path.join(base_dir, "scripts", "build_dashboard.py")
    res3 = subprocess.run([sys.executable, script_dash], capture_output=False)
    if res3.returncode != 0:
        print("\n⚠️ CẢNH BÁO: Bước 3 cập nhật dashboard gặp cảnh báo!")

    print("\n=================================================================")
    print("🎉 QUY TRÌNH CẬP NHẬT BÁO CÁO & DASHBOARD HOÀN TẤT THÀNH CÔNG!")
    print("=================================================================")

if __name__ == "__main__":
    main()
