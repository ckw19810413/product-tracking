#!/bin/bash
# 數位商品銷售追蹤 & 瓶頸調研系統
# 由 cron job 每週一 10:00 AM 自動執行

REPO_DIR="/home/wayne/workspace/hermes-agent/github/ckw19810413/product-tracking"
TRACKER="$REPO_DIR/data"
REPORTS="$REPO_DIR/reports"
RESEARCH="$REPO_DIR/research"
WEEK=$(date +%G-W%V)
TODAY=$(date +%Y-%m-%d)
TIME=$(date +%H:%M:%S)

echo "=== 數位商品銷售追蹤與瓶頸調研開始 ==="

# ──────────────────────────────────────────────
# 階段一：檢查銷售狀態
# ──────────────────────────────────────────────

echo "📊 檢查 Gumroad 銷售狀態..."

# 嘗試從 Gumroad 網頁抓取（如果已上架）
# 實際收入數據需要登入 Gumroad Dashboard 手動輸入或 API 串接

# 建立追蹤目錄
mkdir -p "$TRACKER" "$REPORTS" "$RESEARCH"

# ──────────────────────────────────────────────
# 階段二：產品上架狀態檢查
# ──────────────────────────────────────────────

echo "🔍 檢查產品上架狀態..."

PROMPT_STATUS="🟡 待上架"
COURSE_STATUS="🟡 待上架"
TEMPLATE_STATUS="🟡 待上架"

# 檢查是否有 Gumroad URL（手動填入）
if [ -f "$TRACKER/gumroad-urls.txt" ]; then
    while IFS= read -r line; do
        product=$(echo "$line" | cut -d'|' -f1)
        url=$(echo "$line" | cut -d'|' -f2)
        case "$product" in
            "prompt") PROMPT_STATUS="🟢 已上架 → $url" ;;
            "course") COURSE_STATUS="🟢 已上架 → $url" ;;
            "template") TEMPLATE_STATUS="🟢 已上架 → $url" ;;
        esac
    done < "$TRACKER/gumroad-urls.txt"
fi

# ──────────────────────────────────────────────
# 階段三：瓶頸檢查 & 觸發調研
# ──────────────────────────────────────────────

echo "🚨 瓶頸檢查..."

# 檢查是否觸發調研條件
RESEARCH_TRIGGER=""
BOTTLENECK_TYPE=""
SEVERITY=""

if [ "$PROMPT_STATUS" = "🟡 待上架" ] && [ "$COURSE_STATUS" = "🟡 待上架" ] && [ "$TEMPLATE_STATUS" = "🟡 待上架" ]; then
    RESEARCH_TRIGGER="yes"
    BOTTLENECK_TYPE="product-launch"
    SEVERITY="high"
    echo "⚠️  瓶頸：產品尚未上架，觸發上架策略調研"
elif [ "$PROMPT_STATUS" = "🟢 已上架" ] && [ ! -f "$TRACKER/revenue.json" ]; then
    # 假設已上架但無收入數據 → 假設等待第一筆銷售
    RESEARCH_TRIGGER="yes"
    BOTTLENECK_TYPE="no-revenue"
    SEVERITY="medium"
    echo "⚠️  瓶頸：產品已上架但無收入記錄，觸發行銷策略調研"
fi

# ──────────────────────────────────────────────
# 階段四：生成每週報告
# ──────────────────────────────────────────────

REPORT_FILE="$REPORTS/weekly-${WEEK}.md"

cat > "$REPORT_FILE" <<EOF
# 數位商品每週收入報告
## 第 ${WEEK} 週 (${TODAY})
**報告日期:** ${TODAY}
**生成時間:** ${TIME}

### 📊 財務摘要
| 指標 | 數值 |
|------|------|
| 總收入 | \$0.00（待上架/手動輸入） |
| 新增客戶 | 0 |
| 本週目標 | 確認上架狀態、啟動行銷 |

### 📦 產品上架狀態
| 產品 | 狀態 | 備註 |
|------|------|------|
| AI Prompt 庫 | ${PROMPT_STATUS} | Gumroad/LemonSqueezy |
| AI 實戰課程 | ${COURSE_STATUS} | Gumroad/LemonSqueezy/自己架 |
| 飛書模板市集 | ${TEMPLATE_STATUS} | Gumroad/LemonSqueezy/自己架 |

### 🚨 瓶頸分析
\`瓶頸類型：${BOTTLENECK_TYPE:-none}\`
\`嚴重程度：${SEVERITY:-low}\`

$(if [ "$RESEARCH_TRIGGER" = "yes" ]; then echo "⚠️  **自動觸發深度調研** → 請執行 \`/research trigger\` 或等待 cron 自動執行"; else echo "✅ 無觸發條件"; fi)

### 📋 本週行動項目
- [ ] 完成所有產品上架 Gumroad
- [ ] 建立 Landing Page 並連結 Gumroad
- [ ] 啟動 Twitter/X 行銷（每天 1-2 則推）
- [ ] 加入 Reddit 相關社群提供價值

### 📈 下週目標
- [ ] 上架完成率 100%
- [ ] 啟動第一個行銷渠道
- [ ] 記錄第一筆銷售（如有）

---
*每週一 10:00 AM 自動生成*
*如需手動輸入收入，請編輯 \`data/revenue.json\`*
EOF

echo "✅ 報告已生成: $REPORT_FILE"

# ──────────────────────────────────────────────
# 階段五：執行深度調研（如觸發）
# ──────────────────────────────────────────────

if [ "$RESEARCH_TRIGGER" = "yes" ]; then
    echo "🔬 執行深度調研..."
    
    mkdir -p "$RESEARCH/bottlenecks"
    RESEARCH_DIR="$RESEARCH/bottlenecks/weekly-${WEEK}.md"
    
    cat > "$RESEARCH_DIR" <<'RESEARCHEOF'
# 瓶頸深度調研報告
**觸發日期:** ${TODAY}
**瓶頸類型:** ${BOTTLENECK_TYPE}

## 問題描述
${SEVERITY} 級別瓶頸，需要立即處理。

## 可能的原因分析
1. 產品尚未上架 → 無法產生銷售
2. 缺乏行銷渠道 → 無流量
3. Landing Page 未建立 → 無法轉換

## 建議行動方案
### 優先級 1：上架產品
- 建立 Gumroad 帳號
- 上傳產品檔案
- 設定價格和描述
- 預估時間：2-4 小時

### 優先級 2：建立 Landing Page
- 使用 Next.js 建立產品展示頁面
- 嵌入 Gumroad 購買按鈕
- 增加社會證明（testimonials）
- 預估時間：1-2 天

### 優先級 3：啟動行銷
- Twitter/X 推內容（每天 2 則）
- Reddit 參與討論（每天 1 則）
- LinkedIn 專業社群
- 預估時間：持續進行

## 預期效果
- 上架後第一週：50-100 人看到產品
- 上行銷後第二週：200-500 人看到產品
- 第三週：期望 5-10 筆銷售

## 下次調研日期
${WEEK+1}（如瓶頸未解除）
RESEARCHEOF

    # 替換變數
    sed -i "s/\${TODAY}/$TODAY/g" "$RESEARCH_DIR"
    sed -i "s/\${BOTTLENECK_TYPE}/$BOTTLENECK_TYPE/g" "$RESEARCH_DIR"
    sed -i "s/\${SEVERITY}/$SEVERITY/g" "$RESEARCH_DIR"
    sed -i "s/\${WEEK+1}/$(date -d "+1 week" +%G-W%V 2>/dev/null || echo "N/A")/g" "$RESEARCH_DIR"
    
    echo "✅ 調研報告已生成: $RESEARCH_DIR"
fi

# ──────────────────────────────────────────────
# 階段六：推送 GitHub
# ──────────────────────────────────────────────

cd "$REPO_DIR" || exit 1
git remote get-url origin &>/dev/null || git remote add origin git@github.com:ckw19810413/product-tracking.git

if [ -n "$(git status --porcelain)" ]; then
    git add -A
    git commit -m "chore: weekly tracking ${WEEK} + research report"
    GIT_SSH_COMMAND="ssh -i ~/.ssh/id_ed25519_gh -o IdentitiesOnly=yes" git push origin main 2>&1 | tail -3
    echo "✅ 已推送 GitHub"
else
    echo "ℹ️  無變更"
fi

echo "=== 銷售追蹤與瓶頸調研完成 ==="