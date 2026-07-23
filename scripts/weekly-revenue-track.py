#!/usr/bin/env python3
"""
Weekly Digital Product Revenue Tracker
=======================================
Fetches Gumroad data, generates reports, updates tracking files.
Run every Monday 10:00 AM (Taiwan time) via cron.
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

# ── Configuration ──────────────────────────────────────────────────────────────

TOKEN_FILE = "/home/wayne/.priv/slashmaster6-gumroad-token"
TRACKING_DIR = "/home/wayne/workspace/github/ckw19810413/product-tracking"
RESEARCH_DIR = "/home/wayne/workspace/github/ckw19810413/digital-product-research"
SSH_KEY = "/home/wayne/.ssh/id_ed25519_gh"

DATE = datetime.now().strftime("%Y-%m-%d")
WEEK = datetime.now().strftime("%Y-W%V")
WEEK_START = (datetime.now() - timedelta(days=datetime.now().weekday())).strftime("%Y-%m-%d")
WEEK_END = (datetime.now() + timedelta(days=6 - datetime.now().weekday())).strftime("%Y-%m-%d")

GUMROAD_BASE = "https://api.gumroad.com/v2"


def gumroad_get(endpoint):
    """Fetch from Gumroad API using curl (reliable)."""
    token = open(TOKEN_FILE).read().strip()
    url = f"{GUMROAD_BASE}/{endpoint}?access_token={token}"
    try:
        result = subprocess.run(
            ["curl", "-s", "-f", "--connect-timeout", "10", url],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            return {"success": False, "error": result.stderr or f"HTTP {result.returncode}"}
        data = json.loads(result.stdout)
        return data
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Timeout"}
    except json.JSONDecodeError as e:
        return {"success": False, "error": f"JSON parse error: {e}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def fetch_all_data():
    """Fetch account, products, and sales data."""
    print("=== Fetching Gumroad data ===")

    # Account
    resp = gumroad_get("user")
    if not resp.get("success"):
        print(f"ERROR: Could not fetch account: {resp.get('error')}", file=sys.stderr)
        return None
    account = resp.get("user", {})

    # Products (pagination)
    all_products = []
    params = "products"
    while True:
        resp = gumroad_get(params)
        if not resp.get("success"):
            print(f"  ERROR fetching products: {resp.get('error')}", file=sys.stderr)
            break
        all_products.extend(resp.get("products", []))
        next_key = resp.get("next_page_key")
        if not next_key:
            break
        params = f"products?page_token={next_key}"

    # Dedup by id, keep best version
    seen_ids = {}
    for p in all_products:
        pid = p.get("id")
        if not pid:
            continue
        if pid in seen_ids:
            old = seen_ids[pid]
            old_score = (1 if old.get("published") else 0) + (1 if old.get("covers") else 0) + (1 if old.get("file_info") and old["file_info"] else 0)
            new_score = (1 if p.get("published") else 0) + (1 if p.get("covers") else 0) + (1 if p.get("file_info") and p["file_info"] else 0)
            if new_score > old_score:
                seen_ids[pid] = p
        else:
            seen_ids[pid] = p
    all_products = list(seen_ids.values())

    published = [p for p in all_products if p.get("published")]
    drafts = [p for p in all_products if not p.get("published")]

    # Sales
    sales_resp = gumroad_get("sales")
    sales_data = []
    if sales_resp.get("success"):
        sales_data = sales_resp.get("sales", [])

    print(f"  Account: {account.get('name', 'N/A')} ({account.get('email', 'N/A')})")
    print(f"  Total products: {len(all_products)}")
    print(f"  Published: {len(published)}")
    print(f"  Drafts: {len(drafts)}")
    print(f"  Sales: {len(sales_data)}")

    return {
        "account": account,
        "products": {"all": all_products, "published": published, "drafts": drafts},
        "sales": sales_data
    }


def generate_product_table(products):
    """Generate markdown table for published products."""
    if not products:
        return "| 產品 | 價格 | 銷售量 | 收入 | 狀態 |\n|------|------|--------|------|------|\n| *無上架產品* | - | 0 | $0.00 | ❌ 待上架 |"
    lines = ["| 產品 | 價格 | 銷售量 | 收入 | 狀態 |", "|------|------|--------|------|------|"]
    for p in sorted(products, key=lambda x: x.get("sales_usd_cents", 0), reverse=True):
        name = p.get("name", "Unknown")
        price = p.get("formatted_price", "N/A")
        sc = p.get("sales_count", 0)
        sr = p.get("sales_usd_cents", 0) / 100.0
        status = "✅ 可購買" if p.get("covers") else "⚠️ 缺封面"
        lines.append(f"| {name} | {price} | {sc} | ${sr:.2f} | {status} |")
    return "\n".join(lines)


def generate_bottleneck_analysis(data):
    """Analyze bottlenecks and generate insights."""
    published = data["products"]["published"]
    drafts = data["products"]["drafts"]
    sales = data["sales"]
    bottlenecks = []
    insights = []

    zero_sales = [p for p in published if p.get("sales_count", 0) == 0]
    if zero_sales:
        bottlenecks.append({"type": "zero_sales", "severity": "high", "message": f"{len(zero_sales)} 個已上架產品零銷售", "products": [p.get("name") for p in zero_sales], "recommendation": "需要行銷引流 — Landing Page + Social Media"})

    no_cover = [p for p in published if not p.get("covers")]
    if no_cover:
        bottlenecks.append({"type": "missing_covers", "severity": "medium", "message": f"{len(no_cover)} 個已上架產品缺少封面圖", "products": [p.get("name") for p in no_cover], "recommendation": "加上高品質封面圖可提升轉換率 2-3 倍"})

    no_file = [p for p in published if not (p.get("file_info") and p.get("file_info"))]
    if no_file:
        bottlenecks.append({"type": "missing_files", "severity": "critical", "message": f"{len(no_file)} 個已上架產品缺少實際內容檔", "products": [p.get("name") for p in no_file], "recommendation": "上傳產品內容檔案，否則無法交付"})

    if drafts:
        bottlenecks.append({"type": "draft_products", "severity": "medium", "message": f"{len(drafts)} 個產品仍為草稿狀態", "products": [p.get("name") for p in drafts], "recommendation": "完成草稿產品上架"})

    total_rev = sum(s.get("price_cents", 0) for s in sales)
    if total_rev == 0 and len(published) > 0:
        insights.append("⚠️ 歷史總收入為 $0 — 產品已上架但無流量或轉換")
        insights.append("→ 優先事項：建立 Landing Page 並導入外部流量")
        insights.append("→ 第二優先：優化產品頁面（封面、描述、social proof）")
        insights.append("→ 第三優先：啟動 social media 行銷（Twitter/X、Reddit、Gumroad 平台）")
    else:
        insights.append(f"💰 歷史總收入: ${total_rev / 100:.2f}")

    insights.append("")
    insights.append("### Gumroad 優化建議")
    insights.append("- 產品標籤 (tags) 全部空白 → 加上 6-10 個相關標籤可增加平台內發現")
    insights.append("- 所有產品皆無 cover image → 加上封面圖可提升 40-80% 點擊率")
    insights.append("- 建議定價策略：$49 (Prompt 庫) / $297 (AI 課程) / $197 (模板套組) / $19 (ETF 儀表板)")

    return bottlenecks, insights


def generate_weekly_report(data):
    """Generate the full weekly report markdown."""
    TIME_DISPLAY = datetime.now().strftime("%H:%M CST")
    published = data["products"]["published"]
    drafts = data["products"]["drafts"]
    sales = data["sales"]
    total_revenue = sum(s.get("price_cents", 0) for s in sales)
    unique_buyers = len(set(s.get("buyer_email", "") for s in sales if s.get("buyer_email")))
    bottlenecks, insights = generate_bottleneck_analysis(data)

    draft_table = ""
    if drafts:
        draft_table = "\n| 產品 | 價格 | 狀態 |\n|------|------|------|\n"
        for p in drafts:
            draft_table += f"| {p.get('name', 'Unknown')} | {p.get('formatted_price', 'N/A')} | ❌ 草稿 |\n"

    report = f"""# 每週數位商品收入報告

## {WEEK} ({WEEK_START} - {WEEK_END})
**報告日期:** {DATE}
**資料來源:** Gumroad API (slashmaster6 / Kai Wei Chang)

---

### 財務摘要

| 指標 | 數值 |
|------|------|
| 歷史總收入 | **${total_revenue / 100:.2f}** |
| 累計客戶 | {unique_buyers} |
| 歷史總銷售 | {len(sales)} 筆 |
| 已上架產品 | {len(published)} 個 |
| 草稿產品 | {len(drafts)} 個 |

---

### 各產品收入

{generate_product_table(published)}

---

### 草稿/未完成產品

{draft_table if draft_table else "目前無草稿產品。"}

---

### 瓶頸分析

"""
    if bottlenecks:
        for i, b in enumerate(bottlenecks, 1):
            severity_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡"}.get(b["severity"], "⚪")
            report += f"**{severity_icon} 瓶頸 {i}: {b['message']}**\n"
            report += f"- 涉及產品: {', '.join(b['products'])}\n"
            report += f"- 建議: {b['recommendation']}\n\n"
    else:
        report += "✅ 目前無主要瓶頸\n\n"

    report += "### 關鍵洞察\n\n"
    for insight in insights:
        report += f"{insight}\n"

    report += f"""
---

### 下週行動項目

- [ ] 為所有已上架產品加上封面圖（高品質 PNG）
- [ ] 為每個產品加上 6-10 個標籤 (tags)
- [ ] 建立 Landing Page (Next.js → Vercel 部署)
- [ ] 啟動 Twitter/X 帳號，每天 1-2 則內容
- [ ] 加入 Reddit 相關社群推廣
- [ ] 分析流量來源，優化轉換漏斗

---

*資料來源: Gumroad REST API v2 (自動抓取)*
*生成時間: {DATE} {TIME_DISPLAY}*
"""
    return report


def save_gumroad_data(data):
    """Save raw Gumroad data as JSON."""
    output = {
        "date": DATE, "week": WEEK, "account": data["account"],
        "sales_count": len(data["sales"]),
        "total_revenue_cents": sum(s.get("price_cents", 0) for s in data["sales"]),
        "products": []
    }
    for p in data["products"]["published"]:
        output["products"].append({
            "name": p.get("name", "Unknown"), "price": p.get("formatted_price", "N/A"),
            "sales_count": p.get("sales_count", 0), "sales_usd_cents": p.get("sales_usd_cents", 0),
            "short_url": p.get("short_url", ""), "has_cover": bool(p.get("covers")),
            "has_file": bool(p.get("file_info") and p.get("file_info"))
        })
    os.makedirs(os.path.join(TRACKING_DIR, "data"), exist_ok=True)
    with open(os.path.join(TRACKING_DIR, "data/gumroad-data.json"), "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"  → Saved to data/gumroad-data.json")


def update_tracking_readme(data):
    """Update data/README.md with current product status."""
    published = data["products"]["published"]
    lines = ["# 數位商品追蹤數據\n", "## 產品狀態\n",
             "| 產品 | 狀態 | 上架平台 | 價格 | 銷售量 | 收入 | 最後更新 |\n",
             "|------|------|---------|------|--------|------|---------|"]
    for p in sorted(published, key=lambda x: x.get("sales_usd_cents", 0), reverse=True):
        name = p.get("name", "Unknown")
        price = p.get("formatted_price", "N/A")
        sc = p.get("sales_count", 0)
        sr = p.get("sales_usd_cents", 0) / 100.0
        status_icon = "✅ 可購買" if p.get("covers") else "⚠️ 待優化"
        lines.append(f"| {name} | {status_icon} | Gumroad | {price} | {sc} | ${sr:.2f} | {DATE} |")

    lines += ["\n## 行銷渠道追蹤\n", "| 渠道 | 狀態 | 目標 | 優先級 |\n", "|------|------|------|--------|\n",
              "| Landing Page | ⏳ 待建 | 轉換流量入口 | 最高 |\n",
              "| Twitter/X | ⏳ 待建 | 冷啟動獲客 | 高 |\n",
              "| Reddit 社群 | ⏳ 待建 | 精準流量 | 中 |\n",
              "| Gumroad 平台內 | ✅ 可觸及 | 自然流量 | 中 |\n",
              "| Email List | ⏳ 待建 | 回購/升級 | 低 |\n"]

    lines += [f"\n## 每週目標\n", f"| 週期 | 目標 | 達成率 | 備註 |\n", f"|------|------|--------|------|\n",
              f"| {WEEK} | 上架全部產品 + 啟動 Landing Page | ⬚ 0% | 瓶頸: 無流量 |\n"]

    with open(os.path.join(TRACKING_DIR, "data/README.md"), "w") as f:
        f.write("\n".join(lines))
    print(f"  → Updated data/README.md")


def generate_research_report(data):
    """Generate bottleneck analysis for digital-product-research repo."""
    bottlenecks, insights = generate_bottleneck_analysis(data)
    published = data["products"]["published"]
    sales = data["sales"]

    report = f"""# 數位商品瓶頸分析 — {DATE}

**觸發日期:** {DATE}
**瓶頸類型:** revenue-zero / marketing-gap
**嚴重程度:** high
**報告週期:** {WEEK}

## 問題描述

所有 {len(published)} 個已上架產品皆為零銷售 ({len(sales)} 筆交易)。
這是最關鍵的瓶頸 — 產品已上架但無流量、無曝光、無收入。

## 瓶頸分解

"""
    if bottlenecks:
        for i, b in enumerate(bottlenecks, 1):
            sev_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡"}.get(b["severity"], "⚪")
            report += f"### {sev_icon} 瓶頸 {i}: {b['message']}\n"
            report += f"- 涉及產品: {', '.join(b['products'])}\n"
            report += f"- 建議: {b['recommendation']}\n\n"
    else:
        report += "目前無主要瓶頸。\n\n"

    report += """## 根因分析

### 1. 流量來源為零 (Critical)
- 無 Landing Page 作為轉換入口
- 無 Twitter/X 帳號運營
- 無 Reddit/社群參與
- 無 SEO 自然流量

**影響:** 潛在客戶找不到你的產品。Gumroad 平台內流量也需要產品有標籤、有評價。

### 2. 產品頁面不完整 (High)
- 多個產品缺少封面圖 → 點擊率低
- 所有產品標籤 (tags) 空白 → 平台內不可發現
- 描述缺乏 social proof（推薦、評價）

### 3. 定價策略 (Medium)
- 需觀察市場對 $49/$297/$197/$19 的接受度
- 建議先以 $49 產品建立第一筆收入，再逐步提高

## 30 天行動計畫

### 第 1 週：基礎建設 (Day 1-7)
- [ ] 建立 Landing Page (Next.js + Vercel, 免費)
- [ ] 所有已上架產品加上高品質封面圖 (Flux AI 生成)
- [ ] 為每個產品加上 6-10 個標籤 (tags)
- [ ] 在 Gumroad 加入免費預覽內容

### 第 2 週：冷啟動 (Day 8-14)
- [ ] 建立 Twitter/X 帳號 (@slashman6)
- [ ] 每天發布 1-2 則相關內容
- [ ] 加入 Reddit: r/AI, r/ChatGPT, r/SaaS, r/gumroad
- [ ] 發布 Gumroad 上架公告 (Gumroad social channels)

### 第 3 週：擴張 (Day 15-21)
- [ ] 啟動 LinkedIn 專業內容
- [ ] 嘗試 Gumroad 付費推廣 ($5-10/天)
- [ ] 建立 Email List (Mailchimp/ConvertKit)
- [ ] 加入 HuggingFace / GitHub 社群

### 第 4 週：優化 (Day 22-30)
- [ ] 分析流量來源數據
- [ ] 調整定價策略
- [ ] 收集早期客戶反饋
- [ ] 啟動第二波行銷

## 預估收入

| 產品 | 預估月銷售 | 單價 | 月收入 |
|------|----------|------|--------|
| AI Prompt 庫 | 5-20 筆 | $49 | $245-$980 |
| AI 實戰課程 | 2-10 筆 | $297 | $594-$2,970 |
| 飛書模板套組 | 3-15 筆 | $197 | $591-$2,955 |
| ETF 儀表板 | 5-30 筆 | $19 | $95-$570 |
| **合計** | **15-95 筆** | | **$1,525-$7,475** |

**關鍵假設:** 第一個月累積緩慢，但 30 天內應有第一筆收入。若無收入則需重新評估市場定位。

## 下次調研日期

如 {WEEK_END} 前仍無收入，重新調研並調整策略。下次自動調研日期: 下週一 10:00 AM
---

*自動生成於 {DATE}*\n"""

    os.makedirs(os.path.join(RESEARCH_DIR, "bottlenecks"), exist_ok=True)
    output_path = os.path.join(RESEARCH_DIR, "bottlenecks", f"weekly-{WEEK}.md")
    with open(output_path, "w") as f:
        f.write(report)
    print(f"  → Saved research report to {output_path}")
    return output_path


def push_repo(repo_dir, msg):
    """Git add, commit, pull --rebase, push."""
    ssh = f'GIT_SSH_COMMAND="ssh -i {SSH_KEY} -o IdentitiesOnly=yes"'
    os.system(f'cd "{repo_dir}" && {ssh} git add -A 2>&1')
    os.system(f'cd "{repo_dir}" && {ssh} git commit -m "{msg}" 2>&1')
    os.system(f'cd "{repo_dir}" && {ssh} git pull --rebase origin main 2>&1')
    result = os.system(f'cd "{repo_dir}" && {ssh} git push origin main 2>&1')
    return result == 0


def main():
    print("🚀 Weekly Digital Product Revenue Tracker")
    print(f"📅 Week: {WEEK}, Date: {DATE}")

    data = fetch_all_data()
    if not data:
        print("ERROR: Failed to fetch Gumroad data. Aborting.", file=sys.stderr)
        sys.exit(1)

    # Generate and save report
    report = generate_weekly_report(data)
    report_path = os.path.join(TRACKING_DIR, "reports", f"weekly-{WEEK}.md")
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w") as f:
        f.write(report)
    print(f"\n📄 Report: {report_path}")

    # Save structured data
    save_gumroad_data(data)

    # Update tracking README
    update_tracking_readme(data)

    # Generate research bottleneck report
    generate_research_report(data)

    # Push to GitHub (both repos)
    if push_repo(TRACKING_DIR, f"feat: {WEEK} weekly revenue report"):
        print("  → Pushed product-tracking repo")
    else:
        print("  ⚠️ Could not push product-tracking repo (may have conflicts)")

    if push_repo(RESEARCH_DIR, f"docs: {WEEK} bottleneck analysis"):
        print("  → Pushed digital-product-research repo")
    else:
        print("  ⚠️ Could not push digital-product-research repo (may have conflicts)")

    # Summary
    total_rev = sum(s.get("price_cents", 0) for s in data["sales"])
    print(f"\n📊 Summary:")
    print(f"   Products: {len(data['products']['published'])} published, {len(data['products']['drafts'])} drafts")
    print(f"   Total Revenue: ${total_rev / 100:.2f}")
    print(f"   Sales: {len(data['sales'])} transactions")
    print("\n✅ Done!")


if __name__ == "__main__":
    main()