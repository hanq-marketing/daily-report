# DỰ ÁN MCP - QUẢN LÝ & BÁO CÁO FACEBOOK ADS

Tài liệu này lưu trữ toàn bộ cấu trúc, vai trò của từng file và hướng dẫn vận hành cho dự án tại thư mục `D:\MCP`. Antigravity sẽ tự động đọc file này để nắm trọn vẹn ngữ cảnh của dự án trong mọi phiên làm việc.

---

## 📌 1. Tổng Quan Dự Án
- **Mục tiêu:** Hệ thống tự động hóa thu thập dữ liệu, phân tích chỉ số hiệu quả quảng cáo Facebook Ads, audit chiến dịch, xuất báo cáo định kỳ và trực quan hóa lên Dashboard (GitHub Pages / Local Web).
- **Tài khoản quảng cáo:** `act_1181576440301325`
- **Hạ tầng tích hợp:**
  - **Facebook Graph API:** Lấy số liệu chiến dịch, ad set, ads, insights.
  - **Google Sheets API:** Đồng bộ dữ liệu báo cáo sang Google Sheets qua Service Account.
  - **MegaCRM MCP Server:** Tích hợp với `https://crm.rikkei.edu.vn/api/mcp`.
  - **GitHub Actions & Pages:** Tự động chạy job cập nhật dashboard hàng ngày (`hanq-marketing/daily-report`).

---

## 🗂️ 2. Bản Đồ Cấu Trúc Toàn Bộ File & Thư Mục

### 🔹 Thư mục gốc (`D:\MCP\`)
| File / Thư mục | Chức năng & Vai trò |
|---|---|
| `GEMINI.md` | Bộ nhớ & quy tắc dự án cho AI Agent, tự động tải ngữ cảnh. |
| `README.md` | Tài liệu dự án cho người phát triển. |
| `index.html` | Dashboard HTML/JS trực quan hóa tương tác đa tài khoản, kết nối trực tiếp Google Sheets & Pancake Leads (bộ lọc mốc thời gian, tài khoản, biểu đồ xu hướng, bảng chi tiết phân trang & sort). |
| `.env` | File biến môi trường chứa `FB_TOKEN` và `Github Token` (bảo mật, không commit). |
| `mcp_config.json` | Cấu hình MCP Server kết nối CRM (`megacrm`). |
| `google_service_account.json` | Khóa xác thực Google Service Account để ghi dữ liệu vào Google Sheets. |
| `.gitignore` | Cấu hình loại trừ bảo mật và file tạm khi đồng bộ mã nguồn. |

---

### 🔹 Báo Cáo Facebook (`D:\MCP\Bao_Cao_FB\`)
Chứa các báo cáo phân tích hiệu suất quảng cáo theo từng tháng/chiến dịch:
- **`Bao_Cao_Tong_Hop_Cac_Tai_Khoan_10_2026.md`**: Báo cáo tổng hợp hiệu quả quảng cáo của toàn bộ 10 tài khoản Ads từ 01/10/2026 đến hiện tại (786 dòng chi tiết).
- **`Bao_Cao_Thang_10_2026.md`**: Báo cáo tổng quan và chi tiết kỳ 01/10 – 13/10/2026 (tổng chi tiêu ~5.07 triệu, CTR 0.41%, 34 chuyển đổi, chi tiết 11 chiến dịch).
- **`Bao_Cao_Campaign_Thang_9.md`**: Báo cáo tổng kết hiệu quả chiến dịch tháng 09/2026.
- **`Bao_Cao_Noi_Dung_Thang_9.md`**: Báo cáo phân tích chuyên sâu về nội dung/creative quảng cáo tháng 09/2026.

---

### 🔹 Scripts & Công Cụ Tự Động (`D:\MCP\scripts\`)
- **`run_daily_report.py`**: Script tổng kích hoạt toàn bộ quy trình: kéo API Facebook, đối soát SĐT theo Ad ID và đồng bộ Google Sheets.
- **`generate_multiacct_report.py`**: Thu thập dữ liệu Insights cấp Ad theo ngày của 10 tài khoản, tính số lượng SĐT và xuất CSV/Markdown.
- **`update_google_sheet.py`**: Đối soát và nạp lũy kế dữ liệu các ngày chưa có lên Google Sheets, bảo toàn dữ liệu cũ không xóa.
- **`build_dashboard.py`**: Biên dịch và tạo Dashboard `index.html` tích hợp dữ liệu Google Sheets, hỗ trợ bộ lọc đa tài khoản, thời gian, biểu đồ Chart.js.
- **`fetch_sheet_data.py`**: Script kéo dữ liệu từ Google Sheets (Master Data) và biên dịch cập nhật `index.html` (dùng cho GitHub Actions, không cần Graph API).
- **`push_to_github.py`**: Script tự động đồng bộ mã nguồn, dashboard và dữ liệu lên GitHub repository (`hanq-marketing/daily-report`) qua GitHub REST API.
- **`fetch_fb_data.py`**: Script Python kết nối Facebook Graph API, thu thập dữ liệu insights và ghi vào `data/reportData.json`.
- **`run_audit.ps1`**: Script PowerShell audit toàn diện tài khoản Ads theo các chuẩn mực quảng cáo.
- **`sync_to_sheet.py`**: Đồng bộ dữ liệu từ `reportData.json` lên Google Sheets.
- **`mcp_client.py` & `mcp_query.py`**: Client gọi API MCP Server MegaCRM.
- **`report.py`**: Trích xuất và tạo bảng báo cáo tóm tắt từ dữ liệu thu thập.
- **`fetch_messages.py`**: Thu thập danh sách tin nhắn/lead từ quảng cáo vào `data/messages.txt`.
- **`get_ids.py`, `run_sql.py`**: Các script hỗ trợ kiểm tra ID và truy vấn dữ liệu.
- **`clean_github.py`**: Script dọn dẹp các thư mục dữ liệu cũ trên GitHub repository.
- **`extract.ps1`, `extract2.ps1`, `patch_audit.ps1`, `restore_check.ps1`, `fix_encoding.ps1`**: Các script tiện ích hỗ trợ giải nén, mã hóa và phục hồi script audit.

---

### 🔹 Dữ Liệu (`D:\MCP\data\`)
- **`bao_cao_cac_tai_khoan_10_2026.csv`**: Dữ liệu chi tiết tổng hợp theo ngày x chiến dịch x quảng cáo của 10 tài khoản (kỳ 01/10/2026 - hiện tại).
- **`reportData.json`**: Dữ liệu gốc Facebook Ads thu thập được (nguồn chính nạp vào `index.html`).
- **`report.json`**: Dữ liệu báo cáo tổng hợp.
- **`schema.json`, `schema_utf8.json`**: Cấu trúc dữ liệu CRM & Ads.
- **`messages.txt`**: File văn bản ghi nhận hội thoại/tin nhắn.

---

### 🔹 Tài Liệu Chuẩn & Kỹ Năng (`D:\MCP\docs\`)
- **`skill_daily_ads_report.md`**: Quy trình chuẩn hóa cập nhật báo cáo Facebook Ads đa tài khoản hàng ngày: đọc và bóc tách dữ liệu cuộc trò chuyện từ Pancake API, kết hợp thẻ (tags) phân loại, đếm chính xác số lượng SĐT (1 conv có SĐT = 1 lead), gán vào đúng Ads ID theo ngày phát sinh và đồng bộ lũy kế Google Sheets (bảo toàn dữ liệu cũ).
- **`facebook_ads_audit_report.md`**: Mẫu kết quả đánh giá audit tài khoản Facebook Ads.
- **`skill_facebook_ads_audit.md`**: Hướng dẫn chuẩn hóa quy trình audit Facebook Ads, tiêu chuẩn đo lường (CTR, CPA, Frequency, RoAS,...).
- **`pancake_api.md`**: Tài liệu toàn tập tổng hợp từ Pancake API Reference & Webhooks (Endpoints, schemas, authentication, quickstart).

---

### 🔹 CI/CD & Thư Viện Mở Rộng
- **`.github/workflows/update-dashboard.yml`**: GitHub Actions định kỳ chạy `fetch_sheet_data.py` lấy dữ liệu từ Google Sheets và tự động cập nhật dashboard lên GitHub Pages.
- **`claude-ads-main/`**: Bộ công cụ mở rộng quản lý quảng cáo đa kênh (Meta, Google, TikTok, LinkedIn, YouTube,...).
- **`backup/`**: Thư mục lưu trữ bản sao lưu các phiên bản script cũ.

---

## 🚀 3. Hướng Dẫn Vận Hành Thường Dùng

1. **Cập nhật báo cáo Facebook Ads đa tài khoản & đồng bộ Google Sheets (Khuyên dùng):**
   ```powershell
   python scripts/run_daily_report.py
   ```
2. **Cập nhật dữ liệu Facebook Ads cho Dashboard (cũ):**
   ```powershell
   python scripts/fetch_fb_data.py
   ```
3. **Đồng bộ dữ liệu từ reportData.json sang Google Sheets:**
   ```powershell
   python scripts/sync_to_sheet.py
   ```
4. **Chạy audit tài khoản quảng cáo:**
   ```powershell
   powershell -ExecutionPolicy Bypass -File scripts/run_audit.ps1
   ```
5. **Xem Dashboard:**
   Mở trực tiếp file `index.html` trên trình duyệt.
