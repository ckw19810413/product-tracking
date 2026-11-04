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

# Override any of these via env; defaults resolve relative to $HOME and this repo.
PRIV_DIR = os.environ.get("PRIV_DIR", os.path.expanduser("~/.priv"))
TOKEN_FILE = os.environ.get("GUMROAD_TOKEN_FILE", os.path.join(PRIV_DIR, "slashmaster6-gumroad-token"))
TRACKING_DIR = os.environ.get("TRACKING_DIR", str(Path(__file__).resolve().parent.parent))
RESEARCH_DIR = os.environ.get("RESEARCH_DIR", os.path.join(os.path.dirname(TRACKING_DIR), "digital-product-research"))
SSH_KEY = os.environ.get("SSH_KEY", os.path.expanduser("~/.ssh/id_ed25519_gh"))

DATE = datetime.now().strftime("%Y-%m-%d")
WEEK = datetime.now().strftime("%Y-W%V")
WEEK_START = (datetime.now() - timedelta(days=datetime.now().weekday())).strftime("%Y-%m-%d")
WEEK_END = (datetime.now() + timedelta(days=6 - datetime.now().weekday())).strftime("%Y-%m-%d")

GUMROAD_BASE = "https://api.gumroad.com/v2"


# Account fields written to data/gumroad-data.json (committed): no email/PII.
ACCOUNT_FIELDS = ("name", "display_name", "id", "user_id", "url", "currency_type")


class IncompleteData(Exception):
    """A Gumroad page failed, so totals would be silently wrong."""


def has_product_deliverable(p):
    """Return True if a product has downloadable files or rich_content delivery."""
    return bool(p.get("files") or p.get("rich_content"))


def gumroad_get(endpoint):
    """Fetch from Gumroad API using curl (reliable).

    The token goes in an Authorization header passed on curl's stdin config
    (`-K -`), so it never appears in argv (ps) or in the URL.
    """
    token = open(TOKEN_FILE).read().strip()
    url = f"{GUMROAD_BASE}/{endpoint}"
    try:
        result = subprocess.run(
            ["curl", "-s", "-f", "--connect-timeout", "10", "-K", "-", url],
            input=f'header = "Authorization: Bearer {token}"\n',
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
    """Fetch account, products (with single-product detail), and sales data."""
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
    max_pages = 10
    last_key = None
    for page in range(max_pages):
        resp = gumroad_get(params)
        if not resp.get("success"):
            raise IncompleteData(f"products page {page + 1}: {resp.get('error')}")
        products_page = resp.get("products", [])
        if not products_page:
            break  # No more products
        all_products.extend(products_page)
        next_key = resp.get("next_page_key")
        if not next_key or next_key == last_key:
            break  # No more pages or infinite loop detected
        last_key = next_key
        params = f"products?page_key={next_key}"  # Gumroad ignores page_token
    print(f"  Fetched {len(all_products)} products (across pages)")

    # Enrich each product from the single-product API (`files` and `rich_content`
    # are only populated on `/v2/products/<id>`, whereas list `file_info` is empty).
    for p in all_products:
        pid = p.get("id")
        if not pid:
            continue
        detail_resp = gumroad_get(f"products/{pid}")
        if not detail_resp.get("success"):
            raise IncompleteData(f"product detail {pid}: {detail_resp.get('error')}")
        detail = detail_resp.get("product", {})
        p["files"] = detail.get("files") or []
        p["rich_content"] = detail.get("rich_content") or []
        if "tags" in detail:
            p["tags"] = detail.get("tags") or []

    # Dedup by name (lowercased), keep best version
    # Gumroad creates duplicate entries with different IDs for the same product
    seen_names = {}
    for p in all_products:
        name = p.get("name", "Unknown").strip().lower()
        if not name:
            continue
        if name in seen_names:
            old = seen_names[name]
            old_score = (1 if old.get("published") else 0) + (1 if old.get("covers") else 0) + (1 if has_product_deliverable(old) else 0)
            new_score = (1 if p.get("published") else 0) + (1 if p.get("covers") else 0) + (1 if has_product_deliverable(p) else 0)
            if new_score > old_score:
                seen_names[name] = p
        else:
            seen_names[name] = p
    all_products = list(seen_names.values())
    print(f"  After dedup by name: {len(all_products)} unique products")

    published = [p for p in all_products if p.get("published")]
    drafts = [p for p in all_products if not p.get("published")]

    # Sales (paginated the same way as products)
    sales_data = []
    params = "sales"
    last_key = None
    for page in range(max_pages * 10):
        sales_resp = gumroad_get(params)
        if not sales_resp.get("success"):
            raise IncompleteData(f"sales page {page + 1}: {sales_resp.get('error')}")
        sales_data.extend(sales_resp.get("sales", []))
        next_key = sales_resp.get("next_page_key")
        if not next_key or next_key == last_key:
            break
        last_key = next_key
        params = f"sales?page_key={next_key}"

    print(f"  Account: {account.get('name', 'N/A')}")
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
        status = "✅ 可購買" if (p.get("covers") and has_product_deliverable(p)) else "⚠️ 待檢查"
        lines.append(f"| {name} | {price} | {sc} | ${sr:.2f} | {status} |")
    return "\n".join(lines)


def generate_bottleneck_analysis(data):
    """Analyze bottlenecks and generate data-driven insights."""
    published = data["products"]["published"]
    drafts = data["products"]["drafts"]
    sales = data["sales"]
    bottlenecks = []
    insights = []

    zero_sales = [p for p in published if p.get("sales_count", 0) == 0]
    if zero_sales:
        bottlenecks.append({"type": "zero_sales", "severity": "high", "message": f"{len(zero_sales)} 個已上架產品零銷售", "products": [p.get("name") for p in zero_sales], "recommendation": "優化現有商品頁導購連結與轉換漏斗追蹤"})

    no_cover = [p for p in published if not p.get("covers")]
    if no_cover:
        bottlenecks.append({"type": "missing_covers", "severity": "medium", "message": f"{len(no_cover)} 個已上架產品缺少封面圖", "products": [p.get("name") for p in no_cover], "recommendation": "補齊產品封面圖"})

    no_file = [p for p in published if not has_product_deliverable(p)]
    if no_file:
        bottlenecks.append({"type": "missing_files", "severity": "critical", "message": f"{len(no_file)} 個已上架產品缺少實際內容檔或 Rich Content", "products": [p.get("name") for p in no_file], "recommendation": "上傳產品內容檔案或設定 Rich Content，否則無法交付"})

    no_tags = [p for p in published if not p.get("tags")]
    if no_tags:
        bottlenecks.append({"type": "missing_tags", "severity": "medium", "message": f"{len(no_tags)} 個已上架產品缺少標籤 (tags)", "products": [p.get("name") for p in no_tags], "recommendation": "為缺少標籤的產品補上相關標籤"})

    if drafts:
        bottlenecks.append({"type": "draft_products", "severity": "medium", "message": f"{len(drafts)} 個產品仍為草稿狀態", "products": [p.get("name") for p in drafts], "recommendation": "評估是否完成草稿產品上架或清理"})

    total_rev = sum(s.get("price_cents", 0) for s in sales)
    if total_rev == 0 and len(published) > 0:
        insights.append("⚠️ 歷史總收入為 $0 — 產品已上架且具備交付內容，需聚焦導購轉換")
    else:
        insights.append(f"💰 歷史總收入: ${total_rev / 100:.2f}")

    insights.append("")
    insights.append("### Gumroad 產品健康度（API 實測）")
    insights.append(f"- 內容交付 (files / rich_content)：{len(published) - len(no_file)}/{len(published)} 個已上架產品具備檔案或 Rich Content 交付")
    insights.append(f"- 產品封面 (covers)：{len(published) - len(no_cover)}/{len(published)} 個已上架產品已設定封面圖")
    insights.append(f"- 產品標籤 (tags)：{len(published) - len(no_tags)}/{len(published)} 個已上架產品已設定標籤")

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

    action_lines = [f"- [ ] {b['recommendation']}（{b['message']}）" for b in bottlenecks]
    if not action_lines:
        action_lines.append("- [ ] 持續追蹤各產品頁面轉換率與銷售數據")
    action_block = "\n".join(action_lines)

    report += f"""
---

### 下週行動項目

{action_block}

---

*資料來源: Gumroad REST API v2 (自動抓取)*
*生成時間: {DATE} {TIME_DISPLAY}*
"""
    return report


def save_gumroad_data(data):
    """Save raw Gumroad data as JSON."""
    output = {
        "date": DATE, "week": WEEK,
        "account": {k: data["account"][k] for k in ACCOUNT_FIELDS if k in data["account"]},
        "sales_count": len(data["sales"]),
        "total_revenue_cents": sum(s.get("price_cents", 0) for s in data["sales"]),
        "products": []
    }
    for p in data["products"]["published"]:
        output["products"].append({
            "name": p.get("name", "Unknown"), "price": p.get("formatted_price", "N/A"),
            "sales_count": p.get("sales_count", 0), "sales_usd_cents": p.get("sales_usd_cents", 0),
            "short_url": p.get("short_url", ""), "has_cover": bool(p.get("covers")),
            "has_file": has_product_deliverable(p),
            "files_count": len(p.get("files") or []),
            "has_rich_content": bool(p.get("rich_content")),
            "tags_count": len(p.get("tags") or [])
        })
    os.makedirs(os.path.join(TRACKING_DIR, "data"), exist_ok=True)
    with open(os.path.join(TRACKING_DIR, "data/gumroad-data.json"), "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"  → Saved to data/gumroad-data.json")


def update_tracking_readme(data):
    """Update data/README.md with current product status derived from API data."""
    published = data["products"]["published"]
    lines = ["# 數位商品追蹤數據\n", "## 產品狀態\n",
             "| 產品 | 狀態 | 上架平台 | 價格 | 銷售量 | 收入 | 最後更新 |\n",
             "|------|------|---------|------|--------|------|---------|"]
    for p in sorted(published, key=lambda x: x.get("sales_usd_cents", 0), reverse=True):
        name = p.get("name", "Unknown")
        price = p.get("formatted_price", "N/A")
        sc = p.get("sales_count", 0)
        sr = p.get("sales_usd_cents", 0) / 100.0
        status_icon = "✅ 可購買" if (p.get("covers") and has_product_deliverable(p)) else "⚠️ 待檢查"
        lines.append(f"| {name} | {status_icon} | Gumroad | {price} | {sc} | ${sr:.2f} | {DATE} |")

    with_files = sum(1 for p in published if has_product_deliverable(p))
    with_covers = sum(1 for p in published if p.get("covers"))
    with_tags = sum(1 for p in published if p.get("tags"))
    lines += [
        "\n## 產品目錄健康度（API 實測）\n",
        "| 檢查項目 | 通過數 / 已上架總數 |\n",
        "|----------|---------------------|\n",
        f"| 交付內容 (`files` / `rich_content`) | {with_files} / {len(published)} |\n",
        f"| 產品封面 (`covers`) | {with_covers} / {len(published)} |\n",
        f"| 產品標籤 (`tags`) | {with_tags} / {len(published)} |\n",
    ]

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
**瓶頸類型:** {"revenue-zero / conversion-gap" if not sales else "active-monitoring"}
**嚴重程度:** {"high" if not sales else "low"}
**報告週期:** {WEEK}

## 問題描述

{len(published)} 個已上架產品，共 {len(sales)} 筆交易（Gumroad API，含分頁與單品 API 檢查）。

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

    report += "## 關鍵洞察（API 實測）\n\n"
    for insight in insights:
        report += f"{insight}\n"

    report += """
## 已上架產品與售價

"""
    report += generate_product_table(published)
    report += f"""

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

    try:
        data = fetch_all_data()
    except IncompleteData as e:
        # Abort before writing or pushing anything: a partial page would
        # under-count sales/revenue in a report that looks complete.
        print(f"ERROR: DATA INCOMPLETE ({e}). Aborting, nothing written.", file=sys.stderr)
        sys.exit(1)
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

    if os.environ.get("NO_GIT_PUSH") == "1":
        print("  → Skipping git push (NO_GIT_PUSH=1)")
    else:
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
