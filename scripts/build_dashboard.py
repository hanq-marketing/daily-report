import csv
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
csv_path = os.path.join(base_dir, "data", "bao_cao_cac_tai_khoan_10_2026.csv")
html_path = os.path.join(base_dir, "index.html")

print("Đọc dữ liệu từ CSV...")
rows = []
with open(csv_path, mode="r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for r in reader:
        # Chuẩn hóa kiểu dữ liệu
        row_dict = dict(r)
        for num_field in ["Chi tiêu", "CTR (%)", "CPC", "CPM", "CPA"]:
            try: row_dict[num_field] = float(row_dict.get(num_field, 0))
            except: row_dict[num_field] = 0.0
        for int_field in ["Hiển thị", "Click link", "Tin nhắn", "Lead", "Đăng ký", "Sđt theo campain"]:
            try: row_dict[int_field] = int(float(row_dict.get(int_field, 0)))
            except: row_dict[int_field] = 0
        rows.append(row_dict)

print(f"-> Đã đọc {len(rows)} dòng dữ liệu.")
json_data_str = json.dumps(rows, ensure_ascii=False)

html_content = """<!DOCTYPE html>
<html lang="vi" data-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Meta Ads Multi-Account Dashboard | Báo Cáo Facebook Ads Đa Tài Khoản & Pancake Lead</title>
    <!-- Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <!-- Chart.js & PapaParse -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/papaparse@5.4.1/papaparse.min.js"></script>
    <style>
        :root {
            --bg-base: #090d16;
            --bg-surface: rgba(18, 24, 40, 0.75);
            --bg-surface-solid: #121828;
            --bg-card: rgba(26, 34, 56, 0.65);
            --border-color: rgba(255, 255, 255, 0.08);
            --border-hover: rgba(99, 102, 241, 0.4);
            
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            
            --primary: #6366f1;
            --primary-hover: #4f46e5;
            --primary-light: rgba(99, 102, 241, 0.15);
            
            --success: #10b981;
            --success-light: rgba(16, 185, 129, 0.15);
            --warning: #f59e0b;
            --warning-light: rgba(245, 158, 11, 0.15);
            --danger: #ef4444;
            --danger-light: rgba(239, 68, 68, 0.15);
            --purple: #a855f7;
            --purple-light: rgba(168, 85, 247, 0.15);
            --cyan: #06b6d4;
            
            --radius-sm: 8px;
            --radius-md: 12px;
            --radius-lg: 16px;
            --radius-full: 9999px;
            
            --shadow-card: 0 4px 20px -2px rgba(0, 0, 0, 0.35);
            --shadow-glow: 0 0 25px rgba(99, 102, 241, 0.2);
            --backdrop: blur(14px);
        }

        [data-theme="light"] {
            --bg-base: #f1f5f9;
            --bg-surface: rgba(255, 255, 255, 0.85);
            --bg-surface-solid: #ffffff;
            --bg-card: rgba(255, 255, 255, 0.95);
            --border-color: rgba(0, 0, 0, 0.08);
            --border-hover: rgba(99, 102, 241, 0.5);
            
            --text-primary: #0f172a;
            --text-secondary: #475569;
            --text-muted: #94a3b8;
            
            --primary: #4f46e5;
            --primary-hover: #4338ca;
            --primary-light: rgba(79, 70, 229, 0.1);
            
            --success: #059669;
            --success-light: rgba(5, 150, 105, 0.1);
            --warning: #d97706;
            --warning-light: rgba(217, 119, 6, 0.1);
            --danger: #dc2626;
            --danger-light: rgba(220, 38, 38, 0.1);
            --purple: #9333ea;
            --purple-light: rgba(147, 51, 234, 0.1);
            
            --shadow-card: 0 4px 15px -1px rgba(0, 0, 0, 0.06);
            --shadow-glow: 0 0 20px rgba(79, 70, 229, 0.12);
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: 'Plus Jakarta Sans', sans-serif;
            -webkit-font-smoothing: antialiased;
        }

        body {
            background-color: var(--bg-base);
            color: var(--text-primary);
            min-height: 100vh;
            padding: 1.5rem 2rem;
            transition: background-color 0.3s ease, color 0.3s ease;
        }

        .container {
            max-width: 1720px;
            margin: 0 auto;
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
        }

        /* ─── Header ─── */
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: var(--bg-surface);
            backdrop-filter: var(--backdrop);
            border: 1px solid var(--border-color);
            padding: 1.25rem 1.75rem;
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow-card);
            flex-wrap: wrap;
            gap: 1rem;
        }

        .header-brand {
            display: flex;
            align-items: center;
            gap: 1rem;
        }

        .header-icon {
            width: 46px;
            height: 46px;
            border-radius: var(--radius-md);
            background: linear-gradient(135deg, #6366f1, #a855f7);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
            box-shadow: var(--shadow-glow);
        }

        .header-title h1 {
            font-size: 1.45rem;
            font-weight: 800;
            letter-spacing: -0.02em;
            background: linear-gradient(120deg, var(--text-primary), var(--primary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .header-title p {
            font-size: 0.85rem;
            color: var(--text-secondary);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .header-actions {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            flex-wrap: wrap;
        }

        .badge-status {
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            padding: 0.4rem 0.85rem;
            border-radius: var(--radius-full);
            font-size: 0.8rem;
            font-weight: 600;
            background: var(--success-light);
            color: var(--success);
            border: 1px solid rgba(16, 185, 129, 0.3);
        }

        .badge-status.offline {
            background: var(--warning-light);
            color: var(--warning);
            border-color: rgba(245, 158, 11, 0.3);
        }

        .btn {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.55rem 1rem;
            border-radius: var(--radius-md);
            font-size: 0.85rem;
            font-weight: 600;
            cursor: pointer;
            border: 1px solid var(--border-color);
            background: var(--bg-card);
            color: var(--text-primary);
            transition: all 0.2s ease;
            text-decoration: none;
        }

        .btn:hover {
            border-color: var(--border-hover);
            transform: translateY(-1px);
        }

        .btn-primary {
            background: var(--primary);
            color: #ffffff;
            border-color: var(--primary);
        }

        .btn-primary:hover {
            background: var(--primary-hover);
        }

        /* ─── Filter Section ─── */
        .filters-card {
            background: var(--bg-surface);
            backdrop-filter: var(--backdrop);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-lg);
            padding: 1.25rem 1.75rem;
            box-shadow: var(--shadow-card);
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }

        .filters-row {
            display: flex;
            align-items: center;
            gap: 1.25rem;
            flex-wrap: wrap;
        }

        .filter-group {
            display: flex;
            flex-direction: column;
            gap: 0.35rem;
            min-width: 200px;
            flex: 1;
        }

        .filter-label {
            font-size: 0.78rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-muted);
            display: flex;
            align-items: center;
            gap: 0.4rem;
        }

        .select-input, .date-input, .search-input {
            width: 100%;
            padding: 0.6rem 0.9rem;
            border-radius: var(--radius-md);
            border: 1px solid var(--border-color);
            background: var(--bg-surface-solid);
            color: var(--text-primary);
            font-size: 0.9rem;
            outline: none;
            transition: border-color 0.2s;
        }

        .select-input:focus, .date-input:focus, .search-input:focus {
            border-color: var(--primary);
            box-shadow: 0 0 0 2px var(--primary-light);
        }

        .preset-buttons {
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
            align-items: center;
        }

        .preset-chip {
            padding: 0.35rem 0.75rem;
            border-radius: var(--radius-full);
            font-size: 0.8rem;
            font-weight: 600;
            border: 1px solid var(--border-color);
            background: transparent;
            color: var(--text-secondary);
            cursor: pointer;
            transition: all 0.2s;
        }

        .preset-chip:hover {
            color: var(--text-primary);
            border-color: var(--primary);
        }

        .preset-chip.active {
            background: var(--primary-light);
            border-color: var(--primary);
            color: var(--primary);
        }

        .filter-summary-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-top: 1px solid var(--border-color);
            padding-top: 0.85rem;
            font-size: 0.85rem;
            color: var(--text-secondary);
            flex-wrap: wrap;
            gap: 0.75rem;
        }

        /* ─── KPI Cards Grid ─── */
        .kpi-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 1.25rem;
        }

        .kpi-card {
            background: var(--bg-surface);
            backdrop-filter: var(--backdrop);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-lg);
            padding: 1.25rem 1.5rem;
            box-shadow: var(--shadow-card);
            position: relative;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            gap: 0.4rem;
            transition: transform 0.2s, border-color 0.2s;
        }

        .kpi-card:hover {
            transform: translateY(-2px);
            border-color: var(--border-hover);
        }

        .kpi-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: var(--accent-color, var(--primary));
        }

        .kpi-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .kpi-title {
            font-size: 0.82rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            color: var(--text-muted);
        }

        .kpi-icon {
            font-size: 1.25rem;
            opacity: 0.85;
        }

        .kpi-value {
            font-size: 1.85rem;
            font-weight: 800;
            letter-spacing: -0.02em;
            color: var(--text-primary);
        }

        .kpi-subtext {
            font-size: 0.82rem;
            color: var(--text-secondary);
            display: flex;
            align-items: center;
            gap: 0.4rem;
        }

        .kpi-badge {
            font-weight: 700;
            font-size: 0.78rem;
            padding: 0.15rem 0.45rem;
            border-radius: var(--radius-sm);
        }

        /* ─── Charts Section ─── */
        .charts-grid {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 1.25rem;
        }

        .charts-row-2 {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1.25rem;
        }

        @media (max-width: 1200px) {
            .charts-grid, .charts-row-2 {
                grid-template-columns: 1fr;
            }
        }

        .chart-card {
            background: var(--bg-surface);
            backdrop-filter: var(--backdrop);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-lg);
            padding: 1.5rem;
            box-shadow: var(--shadow-card);
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }

        .chart-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 0.75rem;
        }

        .chart-title {
            font-size: 1rem;
            font-weight: 700;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .chart-subtitle {
            font-size: 0.8rem;
            color: var(--text-muted);
        }

        .chart-container {
            position: relative;
            height: 320px;
            width: 100%;
        }

        /* ─── Data Table Section ─── */
        .table-card {
            background: var(--bg-surface);
            backdrop-filter: var(--backdrop);
            border: 1px solid var(--border-color);
            border-radius: var(--radius-lg);
            padding: 1.5rem;
            box-shadow: var(--shadow-card);
            display: flex;
            flex-direction: column;
            gap: 1.25rem;
        }

        .table-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 1rem;
        }

        .table-title-area {
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }

        .table-title {
            font-size: 1.15rem;
            font-weight: 800;
        }

        .table-count-badge {
            background: var(--primary-light);
            color: var(--primary);
            padding: 0.2rem 0.65rem;
            border-radius: var(--radius-full);
            font-size: 0.8rem;
            font-weight: 700;
        }

        .table-controls {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            flex-wrap: wrap;
        }

        .table-wrapper {
            overflow-x: auto;
            border: 1px solid var(--border-color);
            border-radius: var(--radius-md);
        }

        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.85rem;
            text-align: left;
            white-space: nowrap;
        }

        th {
            background: var(--bg-surface-solid);
            padding: 0.85rem 1rem;
            font-weight: 700;
            color: var(--text-secondary);
            border-bottom: 2px solid var(--border-color);
            cursor: pointer;
            user-select: none;
            transition: color 0.2s;
        }

        th:hover {
            color: var(--primary);
        }

        th.sort-active {
            color: var(--primary);
        }

        td {
            padding: 0.75rem 1rem;
            border-bottom: 1px solid var(--border-color);
            color: var(--text-primary);
        }

        tr:hover td {
            background: rgba(99, 102, 241, 0.04);
        }

        .tag-chip {
            display: inline-block;
            padding: 0.15rem 0.5rem;
            border-radius: var(--radius-sm);
            font-size: 0.72rem;
            font-weight: 600;
            background: rgba(168, 85, 247, 0.15);
            color: #c084fc;
            margin: 0.1rem;
            border: 1px solid rgba(168, 85, 247, 0.3);
        }

        .status-badge {
            display: inline-block;
            padding: 0.2rem 0.55rem;
            border-radius: var(--radius-sm);
            font-size: 0.75rem;
            font-weight: 700;
        }

        .status-active {
            background: var(--success-light);
            color: var(--success);
        }

        .status-paused {
            background: var(--warning-light);
            color: var(--warning);
        }

        .phone-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.25rem;
            padding: 0.2rem 0.6rem;
            border-radius: var(--radius-full);
            font-weight: 800;
            font-size: 0.8rem;
            background: rgba(16, 185, 129, 0.2);
            color: #34d399;
            border: 1px solid rgba(16, 185, 129, 0.4);
        }

        .phone-badge.zero {
            background: transparent;
            color: var(--text-muted);
            border: none;
            font-weight: normal;
        }

        /* ─── Pagination ─── */
        .pagination-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 1rem;
            font-size: 0.85rem;
            color: var(--text-secondary);
        }

        .pagination-buttons {
            display: flex;
            gap: 0.35rem;
        }

        .page-btn {
            padding: 0.4rem 0.75rem;
            border-radius: var(--radius-sm);
            border: 1px solid var(--border-color);
            background: var(--bg-card);
            color: var(--text-primary);
            cursor: pointer;
            font-weight: 600;
            font-size: 0.82rem;
            transition: all 0.2s;
        }

        .page-btn:hover:not(:disabled) {
            border-color: var(--primary);
            color: var(--primary);
        }

        .page-btn.active {
            background: var(--primary);
            color: #fff;
            border-color: var(--primary);
        }

        .page-btn:disabled {
            opacity: 0.4;
            cursor: not-allowed;
        }

        /* Loading Spinner */
        .spinner {
            display: inline-block;
            width: 14px;
            height: 14px;
            border: 2px solid rgba(255,255,255,0.3);
            border-radius: 50%;
            border-top-color: #fff;
            animation: spin 0.8s linear infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- ─── HEADER ─── -->
        <header>
            <div class="header-brand">
                <div class="header-icon">📈</div>
                <div class="header-title">
                    <h1>META ADS MULTI-ACCOUNT DASHBOARD</h1>
                    <p>
                        <span>Hệ thống phân tích hiệu suất quảng cáo đa tài khoản & đối soát SĐT Pancake</span>
                    </p>
                </div>
            </div>
            <div class="header-actions">
                <span id="dataStatusBadge" class="badge-status">
                    <span style="font-size: 0.7rem;">●</span> Đang tải...
                </span>
                <span id="lastUpdatedText" style="font-size: 0.82rem; color: var(--text-muted);"></span>
                <button class="btn btn-primary" id="btnRefresh" title="Kéo dữ liệu mới nhất từ Google Sheets">
                    🔄 Làm mới Google Sheet
                </button>
                <a class="btn" href="https://docs.google.com/spreadsheets/d/1PD3zhqZ2rTZlMi7X3lsCh6fkvNcR-B2kGv0m9L0Fl_4/edit" target="_blank" title="Mở file Google Sheets">
                    📊 Google Sheet
                </a>
                <button class="btn" id="btnThemeToggle" title="Chuyển chế độ Sáng / Tối">
                    🌓
                </button>
            </div>
        </header>

        <!-- ─── FILTER CONTROL BAR ─── -->
        <div class="filters-card">
            <div class="filters-row">
                <!-- Chọn Tài khoản -->
                <div class="filter-group" style="flex: 1.5;">
                    <label class="filter-label">🏢 Chọn Tài Khoản Ads</label>
                    <select id="accountFilter" class="select-input">
                        <option value="ALL">👉 Tất cả các tài khoản (Tổng hợp)</option>
                    </select>
                </div>

                <!-- Từ ngày -->
                <div class="filter-group">
                    <label class="filter-label">📅 Từ ngày</label>
                    <input type="date" id="dateStart" class="date-input">
                </div>

                <!-- Đến ngày -->
                <div class="filter-group">
                    <label class="filter-label">📅 Đến ngày</label>
                    <input type="date" id="dateEnd" class="date-input">
                </div>

                <!-- Trạng thái -->
                <div class="filter-group" style="max-width: 180px;">
                    <label class="filter-label">⚙️ Trạng Thái</label>
                    <select id="statusFilter" class="select-input">
                        <option value="ALL">Tất cả trạng thái</option>
                        <option value="ACTIVE">ACTIVE (Đang chạy)</option>
                        <option value="PAUSED">PAUSED (Tạm dừng)</option>
                    </select>
                </div>

                <!-- Reset Filter -->
                <div style="display: flex; align-items: flex-end;">
                    <button class="btn" id="btnResetFilter" style="height: 42px;">
                        ↺ Đặt lại
                    </button>
                </div>
            </div>

            <!-- Quick Date Presets -->
            <div class="filter-summary-bar">
                <div class="preset-buttons">
                    <span style="font-size: 0.8rem; font-weight: 700; color: var(--text-muted); margin-right: 0.25rem;">Mốc nhanh:</span>
                    <button class="preset-chip active" data-range="all">Toàn bộ kỳ</button>
                    <button class="preset-chip" data-range="this_month">Tháng 10/2026</button>
                    <button class="preset-chip" data-range="last_7">7 ngày qua</button>
                    <button class="preset-chip" data-range="yesterday">Hôm qua</button>
                    <button class="preset-chip" data-range="today">Hôm nay</button>
                </div>
                <div id="filterSummaryText">Đang tải dữ liệu...</div>
            </div>
        </div>

        <!-- ─── KPI CARDS GRID ─── -->
        <div class="kpi-grid">
            <!-- 1. Chi tiêu -->
            <div class="kpi-card" style="--accent-color: #6366f1;">
                <div class="kpi-header">
                    <span class="kpi-title">Tổng Chi Tiêu</span>
                    <span class="kpi-icon">💰</span>
                </div>
                <div class="kpi-value" id="kpiSpend">0 ₫</div>
                <div class="kpi-subtext">
                    <span>Ngân sách TB: <b id="kpiAvgDailyBudget">--</b></span>
                </div>
            </div>

            <!-- 2. Số Điện Thoại Pancake -->
            <div class="kpi-card" style="--accent-color: #10b981;">
                <div class="kpi-header">
                    <span class="kpi-title">SĐT (Pancake Leads)</span>
                    <span class="kpi-icon">📱</span>
                </div>
                <div class="kpi-value" id="kpiPhones" style="color: #34d399;">0</div>
                <div class="kpi-subtext">
                    <span>Chi phí / SĐT: <b id="kpiCostPerPhone" style="color: #34d399;">0 ₫</b></span>
                </div>
            </div>

            <!-- 3. Tin Nhắn -->
            <div class="kpi-card" style="--accent-color: #06b6d4;">
                <div class="kpi-header">
                    <span class="kpi-title">Tin Nhắn Mới</span>
                    <span class="kpi-icon">💬</span>
                </div>
                <div class="kpi-value" id="kpiMessages">0</div>
                <div class="kpi-subtext">
                    <span>Tỷ lệ SĐT/Mess: <b id="kpiPhoneRate">0%</b></span>
                </div>
            </div>

            <!-- 4. Lượt Click & CTR -->
            <div class="kpi-card" style="--accent-color: #a855f7;">
                <div class="kpi-header">
                    <span class="kpi-title">Lượt Click Link & CTR</span>
                    <span class="kpi-icon">🖱️</span>
                </div>
                <div class="kpi-value" id="kpiClicks">0</div>
                <div class="kpi-subtext">
                    <span>CTR TB: <b id="kpiCTR">0.00%</b> • CPC: <b id="kpiCPC">0 ₫</b></span>
                </div>
            </div>

            <!-- 5. Hiển Thị & CPM -->
            <div class="kpi-card" style="--accent-color: #f59e0b;">
                <div class="kpi-header">
                    <span class="kpi-title">Hiển Thị (Impressions)</span>
                    <span class="kpi-icon">👁️</span>
                </div>
                <div class="kpi-value" id="kpiImpressions">0</div>
                <div class="kpi-subtext">
                    <span>CPM TB: <b id="kpiCPM">0 ₫</b></span>
                </div>
            </div>

            <!-- 6. CPA Trung Bình -->
            <div class="kpi-card" style="--accent-color: #ec4899;">
                <div class="kpi-header">
                    <span class="kpi-title">CPA Trung Bình</span>
                    <span class="kpi-icon">🎯</span>
                </div>
                <div class="kpi-value" id="kpiCPA">0 ₫</div>
                <div class="kpi-subtext">
                    <span>Tổng chuyển đổi: <b id="kpiTotalConversions">0</b></span>
                </div>
            </div>
        </div>

        <!-- ─── CHARTS SECTION ─── -->
        <div class="charts-grid">
            <!-- Biểu đồ 1: Xu Hướng Theo Ngày -->
            <div class="chart-card">
                <div class="chart-header">
                    <div>
                        <div class="chart-title">📅 Xu Hướng Hiệu Suất Theo Ngày</div>
                        <div class="chart-subtitle">Chi tiêu (cột) so với Số SĐT Pancake & Tin nhắn mới (đường)</div>
                    </div>
                </div>
                <div class="chart-container">
                    <canvas id="trendChart"></canvas>
                </div>
            </div>

            <!-- Biểu đồ 2: Cơ cấu Thẻ Tags Pancake -->
            <div class="chart-card">
                <div class="chart-header">
                    <div>
                        <div class="chart-title">🏷️ Phân Bố Thẻ Pancake (Tags)</div>
                        <div class="chart-subtitle">Tỷ lệ các nhãn phân loại hội thoại từ khách hàng</div>
                    </div>
                </div>
                <div class="chart-container">
                    <canvas id="tagsChart"></canvas>
                </div>
            </div>
        </div>

        <div class="charts-row-2">
            <!-- Biểu đồ 3: So Sánh Hiệu Quả Các Tài Khoản -->
            <div class="chart-card">
                <div class="chart-header">
                    <div>
                        <div class="chart-title">🏢 So Sánh Hiệu Suất Giữa Các Tài Khoản Ads</div>
                        <div class="chart-subtitle">Chi tiêu (VNĐ) và Số lượng SĐT thu được</div>
                    </div>
                </div>
                <div class="chart-container">
                    <canvas id="accountChart"></canvas>
                </div>
            </div>

            <!-- Biểu đồ 4: Top Chiến Dịch Tạo Nhiều SĐT Nhất -->
            <div class="chart-card">
                <div class="chart-header">
                    <div>
                        <div class="chart-title">🏆 Top Chiến Dịch Tạo Nhiều SĐT Nhất</div>
                        <div class="chart-subtitle">Xếp hạng theo số lượng lead SĐT bóc tách từ Pancake</div>
                    </div>
                </div>
                <div class="chart-container">
                    <canvas id="topCampaignsChart"></canvas>
                </div>
            </div>
        </div>

        <!-- ─── DATA TABLE SECTION ─── -->
        <div class="table-card">
            <div class="table-header">
                <div class="table-title-area">
                    <span class="table-title">📑 Bảng Dữ Liệu Chi Tiết</span>
                    <span class="table-count-badge" id="tableRowCount">0 dòng</span>
                </div>
                <div class="table-controls">
                    <input type="text" id="tableSearchInput" class="search-input" placeholder="🔍 Tìm chiến dịch, ID ad, tag..." style="width: 250px;">
                    <select id="pageSizeSelect" class="select-input" style="width: 120px;">
                        <option value="15">15 dòng/trang</option>
                        <option value="30">30 dòng/trang</option>
                        <option value="50">50 dòng/trang</option>
                        <option value="100">100 dòng/trang</option>
                    </select>
                    <button class="btn" id="btnExportCSV">📥 Xuất CSV</button>
                </div>
            </div>

            <div class="table-wrapper">
                <table id="dataTable">
                    <thead>
                        <tr>
                            <th data-sort="Tài khoản">Tài khoản ⬍</th>
                            <th data-sort="Ngày">Ngày ⬍</th>
                            <th data-sort="Tên chiến dịch">Tên chiến dịch ⬍</th>
                            <th data-sort="Trạng thái">Trạng thái ⬍</th>
                            <th data-sort="Chi tiêu">Chi tiêu (VNĐ) ⬍</th>
                            <th data-sort="Sđt theo campain">SĐT (Pancake) ⬍</th>
                            <th data-sort="Tin nhắn">Tin nhắn ⬍</th>
                            <th data-sort="Click link">Clicks ⬍</th>
                            <th data-sort="CTR (%)">CTR (%) ⬍</th>
                            <th data-sort="CPC">CPC ⬍</th>
                            <th data-sort="CPM">CPM ⬍</th>
                            <th data-sort="CPA">CPA ⬍</th>
                            <th>Tags Pancake</th>
                            <th data-sort="ID quảng cáo">ID quảng cáo ⬍</th>
                        </tr>
                    </thead>
                    <tbody id="tableBody">
                        <!-- Render qua JS -->
                    </tbody>
                </table>
            </div>

            <div class="pagination-bar">
                <div id="paginationInfo">Hiển thị 0 - 0 của 0 dòng</div>
                <div class="pagination-buttons" id="paginationControls"></div>
            </div>
        </div>
    </div>

    <!-- ─── SCRIPT LOGIC ─── -->
    <script>
        // URL Google Sheet GViz CSV (Master Data)
        const GOOGLE_SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1PD3zhqZ2rTZlMi7X3lsCh6fkvNcR-B2kGv0m9L0Fl_4/gviz/tq?tqx=out:csv&sheet=Master%20Data";
        
        // Dữ liệu ban đầu (Local Fallback)
        let RAW_DATA = """ + json_data_str + """;
        let FILTERED_DATA = [];

        // State quản lý bộ lọc
        let currentFilter = {
            account: "ALL",
            dateStart: "",
            dateEnd: "",
            status: "ALL",
            search: ""
        };

        // State phân trang & sort
        let currentPage = 1;
        let pageSize = 15;
        let currentSort = { field: "Ngày", asc: false };

        // Chart instances
        let trendChartInstance = null;
        let tagsChartInstance = null;
        let accountChartInstance = null;
        let topCampaignsChartInstance = null;

        // ─── Formatters ───
        const formatMoney = (val) => new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(val || 0);
        const formatNumber = (val) => new Intl.NumberFormat('vi-VN').format(val || 0);

        // ─── Khởi tạo ứng dụng ───
        document.addEventListener('DOMContentLoaded', () => {
            initTheme();
            setupEventListeners();
            initDateRange();
            populateAccountDropdown();
            applyFilters();
            
            // Tự động kiểm tra và kéo live từ Google Sheets
            fetchLiveData();
        });

        // ─── Quản lý Giao diện Sáng/Tối ───
        function initTheme() {
            const savedTheme = localStorage.getItem('theme') || 'dark';
            document.documentElement.setAttribute('data-theme', savedTheme);
            document.getElementById('btnThemeToggle').addEventListener('click', () => {
                const current = document.documentElement.getAttribute('data-theme');
                const next = current === 'dark' ? 'light' : 'dark';
                document.documentElement.setAttribute('data-theme', next);
                localStorage.setItem('theme', next);
                updateChartsTheme();
            });
        }

        // ─── Thiết lập mốc ngày ───
        function initDateRange() {
            if (!RAW_DATA || RAW_DATA.length === 0) return;
            const dates = RAW_DATA.map(r => r["Ngày"]).filter(Boolean).sort();
            const minDate = dates[0];
            const maxDate = dates[dates.length - 1];
            
            const startInput = document.getElementById('dateStart');
            const endInput = document.getElementById('dateEnd');
            
            startInput.min = minDate;
            startInput.max = maxDate;
            endInput.min = minDate;
            endInput.max = maxDate;

            startInput.value = minDate;
            endInput.value = maxDate;

            currentFilter.dateStart = minDate;
            currentFilter.dateEnd = maxDate;
        }

        // ─── Điền danh sách tài khoản vào Dropdown ───
        function populateAccountDropdown() {
            const select = document.getElementById('accountFilter');
            const currentVal = select.value;
            select.innerHTML = '<option value="ALL">👉 Tất cả các tài khoản (Tổng hợp)</option>';
            
            const accounts = [...new Set(RAW_DATA.map(r => r["Tài khoản"]).filter(Boolean))].sort();
            accounts.forEach(acc => {
                const opt = document.createElement('option');
                opt.value = acc;
                opt.textContent = `🏢 ${acc}`;
                select.appendChild(opt);
            });
            if (accounts.includes(currentVal)) {
                select.value = currentVal;
            }
        }

        // ─── Kéo dữ liệu Live từ Google Sheets ───
        async function fetchLiveData() {
            const badge = document.getElementById('dataStatusBadge');
            const btnRefresh = document.getElementById('btnRefresh');
            badge.className = 'badge-status';
            badge.innerHTML = '<span class="spinner"></span> Đang đồng bộ...';
            btnRefresh.disabled = true;

            try {
                const resp = await fetch(GOOGLE_SHEET_CSV_URL, { cache: 'no-cache' });
                if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
                const csvText = await resp.text();

                Papa.parse(csvText, {
                    header: true,
                    dynamicTyping: true,
                    skipEmptyLines: true,
                    complete: (results) => {
                        if (results.data && results.data.length > 0) {
                            // Map dữ liệu từ Sheet sang format nội bộ
                            RAW_DATA = results.data.map(r => ({
                                "Tài khoản": r["Account Name"] || r["Tài khoản"] || "",
                                "ID tài khoản": r["Account ID"] || r["ID tài khoản"] || "",
                                "Ngày": String(r["Ngày"] || "").trim(),
                                "Campaign ID": String(r["Campaign ID"] || ""),
                                "Tên chiến dịch": r["Tên chiến dịch"] || "",
                                "Trạng thái": r["Trạng thái"] || "UNKNOWN",
                                "Ngân sách/ngày": r["Ngân sách/ngày"] || "",
                                "Chi tiêu": parseFloat(r["Chi tiêu"] || 0),
                                "Hiển thị": parseInt(r["Hiển thị"] || 0),
                                "Click link": parseInt(r["Click link"] || 0),
                                "CTR (%)": parseFloat(r["CTR (%)"] || 0),
                                "CPC": parseFloat(r["CPC"] || 0),
                                "CPM": parseFloat(r["CPM"] || 0),
                                "Tin nhắn": parseInt(r["Tin nhắn"] || 0),
                                "Lead": parseInt(r["Lead"] || 0),
                                "Đăng ký": parseInt(r["Đăng ký"] || 0),
                                "CPA": parseFloat(r["CPA"] || 0),
                                "Cập nhật lúc": r["Cập nhật lúc"] || "",
                                "ID quảng cáo": String(r["ID quảng cáo"] || ""),
                                "Tên quảng cáo": r["Tên quảng cáo"] || "",
                                "Sđt theo campain": parseInt(r["Sđt theo campain"] || 0),
                                "Tags Pancake": r["Tags Pancake"] || ""
                            }));

                            badge.className = 'badge-status';
                            badge.innerHTML = '🟢 Google Sheets (Trực tiếp)';
                            document.getElementById('lastUpdatedText').textContent = `Lần đồng bộ cuối: ${new Date().toLocaleTimeString('vi-VN')}`;
                            populateAccountDropdown();
                            initDateRange();
                            applyFilters();
                        }
                    },
                    error: (err) => {
                        throw err;
                    }
                });
            } catch (e) {
                console.warn("Không thể fetch trực tiếp Google Sheets (có thể do offline hoặc CORS file://):", e);
                badge.className = 'badge-status offline';
                badge.innerHTML = '🟡 Dữ liệu Cục bộ (Offline)';
                document.getElementById('lastUpdatedText').textContent = 'Sử dụng bản lưu mới nhất';
            } finally {
                btnRefresh.disabled = false;
            }
        }

        // ─── Xử lý Lọc & Tìm kiếm ───
        function applyFilters() {
            currentFilter.account = document.getElementById('accountFilter').value;
            currentFilter.dateStart = document.getElementById('dateStart').value;
            currentFilter.dateEnd = document.getElementById('dateEnd').value;
            currentFilter.status = document.getElementById('statusFilter').value;
            currentFilter.search = document.getElementById('tableSearchInput').value.toLowerCase().trim();

            FILTERED_DATA = RAW_DATA.filter(row => {
                // Lọc tài khoản
                if (currentFilter.account !== "ALL" && row["Tài khoản"] !== currentFilter.account) {
                    return false;
                }
                // Lọc ngày
                const rowDate = row["Ngày"];
                if (currentFilter.dateStart && rowDate < currentFilter.dateStart) return false;
                if (currentFilter.dateEnd && rowDate > currentFilter.dateEnd) return false;
                
                // Lọc trạng thái
                if (currentFilter.status !== "ALL" && row["Trạng thái"] !== currentFilter.status) {
                    return false;
                }

                // Lọc search
                if (currentFilter.search) {
                    const q = currentFilter.search;
                    const match = (
                        (row["Tên chiến dịch"] && row["Tên chiến dịch"].toLowerCase().includes(q)) ||
                        (row["Tên quảng cáo"] && row["Tên quảng cáo"].toLowerCase().includes(q)) ||
                        (row["ID quảng cáo"] && row["ID quảng cáo"].includes(q)) ||
                        (row["Tags Pancake"] && row["Tags Pancake"].toLowerCase().includes(q)) ||
                        (row["Tài khoản"] && row["Tài khoản"].toLowerCase().includes(q))
                    );
                    if (!match) return false;
                }
                return true;
            });

            currentPage = 1;
            updateKPIs();
            renderCharts();
            renderTable();
            updateFilterSummaryText();
        }

        function updateFilterSummaryText() {
            const accText = currentFilter.account === "ALL" ? "Tất cả tài khoản" : currentFilter.account;
            const dateText = `${currentFilter.dateStart} → ${currentFilter.dateEnd}`;
            document.getElementById('filterSummaryText').innerHTML = `Đang lọc: <b>${accText}</b> | <b>${dateText}</b> (Khớp <b>${FILTERED_DATA.length}</b> / ${RAW_DATA.length} dòng)`;
        }

        // ─── Cập nhật KPI Metrics ───
        function updateKPIs() {
            const totalSpend = FILTERED_DATA.reduce((sum, r) => sum + (r["Chi tiêu"] || 0), 0);
            const totalImpressions = FILTERED_DATA.reduce((sum, r) => sum + (r["Hiển thị"] || 0), 0);
            const totalClicks = FILTERED_DATA.reduce((sum, r) => sum + (r["Click link"] || 0), 0);
            const totalMessages = FILTERED_DATA.reduce((sum, r) => sum + (r["Tin nhắn"] || 0), 0);
            const totalPhones = FILTERED_DATA.reduce((sum, r) => sum + (r["Sđt theo campain"] || 0), 0);
            const totalLeads = FILTERED_DATA.reduce((sum, r) => sum + (r["Lead"] || 0), 0);
            const totalRegs = FILTERED_DATA.reduce((sum, r) => sum + (r["Đăng ký"] || 0), 0);

            const ctr = totalImpressions > 0 ? (totalClicks / totalImpressions * 100) : 0;
            const cpc = totalClicks > 0 ? (totalSpend / totalClicks) : 0;
            const cpm = totalImpressions > 0 ? (totalSpend / totalImpressions * 1000) : 0;
            
            const costPerPhone = totalPhones > 0 ? (totalSpend / totalPhones) : 0;
            const phoneRate = totalMessages > 0 ? (totalPhones / totalMessages * 100) : 0;
            const totalConversions = totalMessages + totalPhones + totalLeads + totalRegs;
            const avgCPA = totalConversions > 0 ? (totalSpend / totalConversions) : 0;

            document.getElementById('kpiSpend').textContent = formatMoney(totalSpend);
            document.getElementById('kpiPhones').textContent = formatNumber(totalPhones);
            document.getElementById('kpiCostPerPhone').textContent = totalPhones > 0 ? formatMoney(costPerPhone) : '--';
            document.getElementById('kpiMessages').textContent = formatNumber(totalMessages);
            document.getElementById('kpiPhoneRate').textContent = `${phoneRate.toFixed(1)}%`;
            document.getElementById('kpiClicks').textContent = formatNumber(totalClicks);
            document.getElementById('kpiCTR').textContent = `${ctr.toFixed(2)}%`;
            document.getElementById('kpiCPC').textContent = formatMoney(cpc);
            document.getElementById('kpiImpressions').textContent = formatNumber(totalImpressions);
            document.getElementById('kpiCPM').textContent = formatMoney(cpm);
            document.getElementById('kpiCPA').textContent = formatMoney(avgCPA);
            document.getElementById('kpiTotalConversions').textContent = formatNumber(totalConversions);

            // Ngân sách ước tính
            const datesCount = new Set(FILTERED_DATA.map(r => r["Ngày"])).size || 1;
            const avgDaily = totalSpend / datesCount;
            document.getElementById('kpiAvgDailyBudget').textContent = `${formatMoney(avgDaily)}/ngày`;
        }

        // ─── Biểu đồ trực quan hóa ───
        function getChartColors() {
            const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
            return {
                text: isDark ? '#94a3b8' : '#475569',
                grid: isDark ? 'rgba(255, 255, 255, 0.06)' : 'rgba(0, 0, 0, 0.06)',
            };
        }

        function updateChartsTheme() {
            renderCharts();
        }

        function renderCharts() {
            renderTrendChart();
            renderTagsChart();
            renderAccountChart();
            renderTopCampaignsChart();
        }

        // 1. Trend Chart (Ngày x Chi tiêu & SĐT)
        function renderTrendChart() {
            const ctx = document.getElementById('trendChart').getContext('2d');
            const colors = getChartColors();

            // Tổng hợp theo ngày
            const dailyData = {};
            FILTERED_DATA.forEach(r => {
                const d = r["Ngày"];
                if (!d) return;
                if (!dailyData[d]) dailyData[d] = { spend: 0, phones: 0, messages: 0 };
                dailyData[d].spend += (r["Chi tiêu"] || 0);
                dailyData[d].phones += (r["Sđt theo campain"] || 0);
                dailyData[d].messages += (r["Tin nhắn"] || 0);
            });

            const sortedDates = Object.keys(dailyData).sort();
            const spendArr = sortedDates.map(d => dailyData[d].spend);
            const phonesArr = sortedDates.map(d => dailyData[d].phones);
            const messagesArr = sortedDates.map(d => dailyData[d].messages);

            if (trendChartInstance) trendChartInstance.destroy();

            trendChartInstance = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: sortedDates.map(d => d.slice(5)), // MM-DD
                    datasets: [
                        {
                            label: 'Chi tiêu (VNĐ)',
                            data: spendArr,
                            backgroundColor: 'rgba(99, 102, 241, 0.45)',
                            borderColor: '#6366f1',
                            borderWidth: 1.5,
                            borderRadius: 6,
                            yAxisID: 'ySpend',
                            order: 2
                        },
                        {
                            label: 'SĐT (Pancake)',
                            data: phonesArr,
                            type: 'line',
                            borderColor: '#10b981',
                            backgroundColor: '#10b981',
                            pointRadius: 4,
                            pointHoverRadius: 6,
                            borderWidth: 2.5,
                            tension: 0.3,
                            yAxisID: 'yCount',
                            order: 1
                        },
                        {
                            label: 'Tin nhắn',
                            data: messagesArr,
                            type: 'line',
                            borderColor: '#06b6d4',
                            backgroundColor: '#06b6d4',
                            pointRadius: 3,
                            borderWidth: 2,
                            borderDash: [4, 4],
                            tension: 0.3,
                            yAxisID: 'yCount',
                            order: 1
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: { mode: 'index', intersect: false },
                    plugins: {
                        legend: { position: 'top', labels: { color: colors.text, font: { weight: 600 } } },
                        tooltip: {
                            callbacks: {
                                label: (ctx) => {
                                    if (ctx.dataset.yAxisID === 'ySpend') {
                                        return `${ctx.dataset.label}: ${formatMoney(ctx.raw)}`;
                                    }
                                    return `${ctx.dataset.label}: ${formatNumber(ctx.raw)}`;
                                }
                            }
                        }
                    },
                    scales: {
                        x: { grid: { color: colors.grid }, ticks: { color: colors.text } },
                        ySpend: {
                            type: 'linear',
                            position: 'left',
                            grid: { color: colors.grid },
                            ticks: {
                                color: colors.text,
                                callback: val => `${(val / 1e6).toFixed(1)}M`
                            }
                        },
                        yCount: {
                            type: 'linear',
                            position: 'right',
                            grid: { drawOnChartArea: false },
                            ticks: { color: colors.text, precision: 0 }
                        }
                    }
                }
            });
        }

        // 2. Tags Chart (Pancake Tags Donut)
        function renderTagsChart() {
            const ctx = document.getElementById('tagsChart').getContext('2d');
            const colors = getChartColors();

            const tagCounts = {};
            FILTERED_DATA.forEach(r => {
                const tagsStr = r["Tags Pancake"] || "";
                if (!tagsStr) return;
                const tagsList = tagsStr.split(',').map(t => t.trim()).filter(Boolean);
                tagsList.forEach(t => {
                    tagCounts[t] = (tagCounts[t] || 0) + 1;
                });
            });

            const sortedTags = Object.entries(tagCounts).sort((a, b) => b[1] - a[1]).slice(0, 8);
            const labels = sortedTags.map(x => x[0]);
            const dataVals = sortedTags.map(x => x[1]);

            if (tagsChartInstance) tagsChartInstance.destroy();

            const palette = ['#6366f1', '#10b981', '#06b6d4', '#f59e0b', '#ec4899', '#a855f7', '#3b82f6', '#84cc16'];

            tagsChartInstance = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: labels.length ? labels : ['Chưa có thẻ'],
                    datasets: [{
                        data: dataVals.length ? dataVals : [1],
                        backgroundColor: palette,
                        borderWidth: 2,
                        borderColor: 'transparent'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'right', labels: { color: colors.text, font: { size: 11, weight: 600 } } }
                    },
                    cutout: '65%'
                }
            });
        }

        // 3. Account Comparison Chart
        function renderAccountChart() {
            const ctx = document.getElementById('accountChart').getContext('2d');
            const colors = getChartColors();

            const accMap = {};
            FILTERED_DATA.forEach(r => {
                const a = r["Tài khoản"];
                if (!a) return;
                if (!accMap[a]) accMap[a] = { spend: 0, phones: 0 };
                accMap[a].spend += (r["Chi tiêu"] || 0);
                accMap[a].phones += (r["Sđt theo campain"] || 0);
            });

            const sortedAccs = Object.keys(accMap).sort((a, b) => accMap[b].spend - accMap[a].spend);
            const spendData = sortedAccs.map(a => accMap[a].spend);
            const phoneData = sortedAccs.map(a => accMap[a].phones);

            if (accountChartInstance) accountChartInstance.destroy();

            accountChartInstance = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: sortedAccs,
                    datasets: [
                        {
                            label: 'Chi tiêu (VNĐ)',
                            data: spendData,
                            backgroundColor: 'rgba(99, 102, 241, 0.7)',
                            borderRadius: 6,
                            yAxisID: 'ySpend'
                        },
                        {
                            label: 'SĐT (Leads)',
                            data: phoneData,
                            backgroundColor: 'rgba(16, 185, 129, 0.8)',
                            borderRadius: 6,
                            yAxisID: 'yCount'
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'top', labels: { color: colors.text, font: { weight: 600 } } },
                        tooltip: {
                            callbacks: {
                                label: (ctx) => ctx.datasetIndex === 0 ? `Chi tiêu: ${formatMoney(ctx.raw)}` : `SĐT: ${formatNumber(ctx.raw)}`
                            }
                        }
                    },
                    scales: {
                        x: { grid: { color: colors.grid }, ticks: { color: colors.text } },
                        ySpend: {
                            type: 'linear',
                            position: 'left',
                            grid: { color: colors.grid },
                            ticks: { color: colors.text, callback: val => `${(val / 1e6).toFixed(0)}M` }
                        },
                        yCount: {
                            type: 'linear',
                            position: 'right',
                            grid: { drawOnChartArea: false },
                            ticks: { color: colors.text, precision: 0 }
                        }
                    }
                }
            });
        }

        // 4. Top Campaigns Chart
        function renderTopCampaignsChart() {
            const ctx = document.getElementById('topCampaignsChart').getContext('2d');
            const colors = getChartColors();

            const campMap = {};
            FILTERED_DATA.forEach(r => {
                const c = r["Tên chiến dịch"];
                if (!c) return;
                if (!campMap[c]) campMap[c] = { phones: 0, spend: 0 };
                campMap[c].phones += (r["Sđt theo campain"] || 0);
                campMap[c].spend += (r["Chi tiêu"] || 0);
            });

            const topCamps = Object.entries(campMap)
                .sort((a, b) => b[1].phones - a[1].phones || b[1].spend - a[1].spend)
                .slice(0, 8);

            const labels = topCamps.map(x => x[0].length > 25 ? x[0].slice(0, 23) + '…' : x[0]);
            const phones = topCamps.map(x => x[1].phones);

            if (topCampaignsChartInstance) topCampaignsChartInstance.destroy();

            topCampaignsChartInstance = new Chart(ctx, {
                type: 'bar',
                indexAxis: 'y',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Số SĐT thu được',
                        data: phones,
                        backgroundColor: '#10b981',
                        borderRadius: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        x: { grid: { color: colors.grid }, ticks: { color: colors.text, precision: 0 } },
                        y: { grid: { color: colors.grid }, ticks: { color: colors.text } }
                    }
                }
            });
        }

        // ─── Bảng Dữ Liệu Chi Tiết ───
        function renderTable() {
            const tbody = document.getElementById('tableBody');
            tbody.innerHTML = '';

            // Sắp xếp dữ liệu
            const sorted = [...FILTERED_DATA].sort((a, b) => {
                let vA = a[currentSort.field];
                let vB = b[currentSort.field];
                if (typeof vA === 'string') {
                    return currentSort.asc ? vA.localeCompare(vB) : vB.localeCompare(vA);
                }
                vA = vA || 0;
                vB = vB || 0;
                return currentSort.asc ? vA - vB : vB - vA;
            });

            // Phân trang
            const total = sorted.length;
            document.getElementById('tableRowCount').textContent = `${formatNumber(total)} dòng`;
            const startIdx = (currentPage - 1) * pageSize;
            const endIdx = Math.min(startIdx + pageSize, total);
            const pageData = sorted.slice(startIdx, endIdx);

            if (pageData.length === 0) {
                tbody.innerHTML = `<tr><td colspan="14" style="text-align: center; padding: 2rem; color: var(--text-muted);">Không tìm thấy dữ liệu phù hợp với bộ lọc hiện tại.</td></tr>`;
                document.getElementById('paginationInfo').textContent = 'Hiển thị 0 dòng';
                document.getElementById('paginationControls').innerHTML = '';
                return;
            }

            pageData.forEach(r => {
                const tr = document.createElement('tr');
                
                // Tags chips
                const tagsStr = r["Tags Pancake"] || "";
                let tagsHtml = "--";
                if (tagsStr) {
                    tagsHtml = tagsStr.split(',').map(t => `<span class="tag-chip">${t.trim()}</span>`).join('');
                }

                // Trạng thái badge
                const statusClass = r["Trạng thái"] === 'ACTIVE' ? 'status-active' : 'status-paused';
                const statusHtml = `<span class="status-badge ${statusClass}">${r["Trạng thái"]}</span>`;

                // SĐT badge
                const sdtVal = r["Sđt theo campain"] || 0;
                const sdtHtml = sdtVal > 0 
                    ? `<span class="phone-badge">📱 ${sdtVal}</span>` 
                    : `<span class="phone-badge zero">0</span>`;

                tr.innerHTML = `
                    <td><b>${r["Tài khoản"]}</b></td>
                    <td>${r["Ngày"]}</td>
                    <td title="${r["Tên chiến dịch"]}">${(r["Tên chiến dịch"] || "").slice(0, 32)}${(r["Tên chiến dịch"] || "").length > 32 ? '…' : ''}</td>
                    <td>${statusHtml}</td>
                    <td><b>${formatMoney(r["Chi tiêu"])}</b></td>
                    <td>${sdtHtml}</td>
                    <td>${formatNumber(r["Tin nhắn"])}</td>
                    <td>${formatNumber(r["Click link"])}</td>
                    <td>${(r["CTR (%)"] || 0).toFixed(2)}%</td>
                    <td>${formatMoney(r["CPC"])}</td>
                    <td>${formatMoney(r["CPM"])}</td>
                    <td>${formatMoney(r["CPA"])}</td>
                    <td>${tagsHtml}</td>
                    <td><code style="font-size: 0.75rem;">${r["ID quảng cáo"]}</code></td>
                `;
                tbody.appendChild(tr);
            });

            document.getElementById('paginationInfo').textContent = `Hiển thị ${startIdx + 1} - ${endIdx} trong tổng số ${formatNumber(total)} dòng`;
            renderPaginationControls(total);
        }

        function renderPaginationControls(total) {
            const container = document.getElementById('paginationControls');
            container.innerHTML = '';
            const totalPages = Math.ceil(total / pageSize);
            if (totalPages <= 1) return;

            const prevBtn = document.createElement('button');
            prevBtn.className = 'page-btn';
            prevBtn.innerHTML = '← Trước';
            prevBtn.disabled = currentPage === 1;
            prevBtn.onclick = () => { currentPage--; renderTable(); };
            container.appendChild(prevBtn);

            // Các trang rút gọn
            let pages = [];
            if (totalPages <= 7) {
                pages = Array.from({ length: totalPages }, (_, i) => i + 1);
            } else {
                if (currentPage <= 4) pages = [1, 2, 3, 4, 5, '...', totalPages];
                else if (currentPage >= totalPages - 3) pages = [1, '...', totalPages - 4, totalPages - 3, totalPages - 2, totalPages - 1, totalPages];
                else pages = [1, '...', currentPage - 1, currentPage, currentPage + 1, '...', totalPages];
            }

            pages.forEach(p => {
                if (p === '...') {
                    const span = document.createElement('span');
                    span.textContent = '...';
                    span.style.padding = '0.4rem 0.5rem';
                    span.style.color = 'var(--text-muted)';
                    container.appendChild(span);
                } else {
                    const btn = document.createElement('button');
                    btn.className = `page-btn ${p === currentPage ? 'active' : ''}`;
                    btn.textContent = p;
                    btn.onclick = () => { currentPage = p; renderTable(); };
                    container.appendChild(btn);
                }
            });

            const nextBtn = document.createElement('button');
            nextBtn.className = 'page-btn';
            nextBtn.innerHTML = 'Sau →';
            nextBtn.disabled = currentPage === totalPages;
            nextBtn.onclick = () => { currentPage++; renderTable(); };
            container.appendChild(nextBtn);
        }

        // ─── Thiết lập Event Listeners ───
        function setupEventListeners() {
            // Bộ lọc thay đổi
            document.getElementById('accountFilter').addEventListener('change', applyFilters);
            document.getElementById('dateStart').addEventListener('change', applyFilters);
            document.getElementById('dateEnd').addEventListener('change', applyFilters);
            document.getElementById('statusFilter').addEventListener('change', applyFilters);
            document.getElementById('tableSearchInput').addEventListener('input', applyFilters);
            
            document.getElementById('pageSizeSelect').addEventListener('change', (e) => {
                pageSize = parseInt(e.target.value);
                currentPage = 1;
                renderTable();
            });

            // Preset Buttons
            document.querySelectorAll('.preset-chip').forEach(btn => {
                btn.addEventListener('click', () => {
                    document.querySelectorAll('.preset-chip').forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');

                    const range = btn.getAttribute('data-range');
                    const dates = RAW_DATA.map(r => r["Ngày"]).filter(Boolean).sort();
                    const minDate = dates[0];
                    const maxDate = dates[dates.length - 1];

                    const startInput = document.getElementById('dateStart');
                    const endInput = document.getElementById('dateEnd');

                    if (range === 'all') {
                        startInput.value = minDate;
                        endInput.value = maxDate;
                    } else if (range === 'this_month') {
                        startInput.value = '2026-10-01';
                        endInput.value = maxDate;
                    } else if (range === 'last_7') {
                        const d = new Date(maxDate);
                        d.setDate(d.getDate() - 6);
                        startInput.value = d.toISOString().slice(0, 10);
                        endInput.value = maxDate;
                    } else if (range === 'today') {
                        startInput.value = maxDate;
                        endInput.value = maxDate;
                    } else if (range === 'yesterday') {
                        const d = new Date(maxDate);
                        d.setDate(d.getDate() - 1);
                        const str = d.toISOString().slice(0, 10);
                        startInput.value = str;
                        endInput.value = str;
                    }
                    applyFilters();
                });
            });

            // Reset Filter
            document.getElementById('btnResetFilter').addEventListener('click', () => {
                document.getElementById('accountFilter').value = 'ALL';
                document.getElementById('statusFilter').value = 'ALL';
                document.getElementById('tableSearchInput').value = '';
                document.querySelector('.preset-chip[data-range="all"]').click();
            });

            // Nút Refresh
            document.getElementById('btnRefresh').addEventListener('click', fetchLiveData);

            // Table Sorting
            document.querySelectorAll('th[data-sort]').forEach(th => {
                th.addEventListener('click', () => {
                    const field = th.getAttribute('data-sort');
                    if (currentSort.field === field) {
                        currentSort.asc = !currentSort.asc;
                    } else {
                        currentSort.field = field;
                        currentSort.asc = false; // default desc cho số
                    }
                    renderTable();
                });
            });

            // Xuất CSV
            document.getElementById('btnExportCSV').addEventListener('click', () => {
                if (!FILTERED_DATA.length) return alert('Không có dữ liệu để xuất!');
                const csv = Papa.unparse(FILTERED_DATA);
                const blob = new Blob(["\\uFEFF" + csv], { type: 'text/csv;charset=utf-8;' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `bao_cao_ads_${currentFilter.account}_${currentFilter.dateStart}_${currentFilter.dateEnd}.csv`;
                a.click();
            });
        }
    </script>
</body>
</html>
"""

with open(html_path, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"✅ Đã tạo thành công file Dashboard tại: {html_path}")
print(f"Dung lượng file: {os.path.getsize(html_path) / 1024:.1f} KB")
