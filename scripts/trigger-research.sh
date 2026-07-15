#!/bin/bash
# 觸發數位商品銷售深度調研
# 手動觸發或當銷售遇到瓶頸時執行

REPO_DIR="/home/wayne/workspace/hermes-agent/github/ckw19810413/product-tracking"
RESEARCH_DIR="$REPO_DIR/research"
DATA_DIR="$REPO_DIR/data"
WEEK=$(date +%G-W%V)
TODAY=$(date +%Y-%m-%d)

echo "=== 觸發銷售深度調研 ==="

# 建立調研分類目錄
mkdir -p "$RESEARCH_DIR/{bottlenecks,competitor-analysis,marketing-channels,promotional-strategies,pricing-research}"

# ──────────────────────────────────────────────
# 讀取產品上架狀態
# ──────────────────────────────────────────────

PROMPT_URL=""
COURSE_URL=""
TEMPLATE_URL=""

if [ -f "$DATA_DIR/gumroad-urls.txt" ]; then
    PROMPT_URL=$(grep "prompt" "$DATA_DIR/gumroad-urls.txt" | cut -d'|' -f2 || true)
    COURSE_URL=$(grep "course" "$DATA_DIR/gumroad-urls.txt" | cut -d'|' -f2 || true)
    TEMPLATE_URL=$(grep "template" "$DATA_DIR/gumroad-urls.txt" | cut -d'|' -f2 || true)
fi

# ──────────────────────────────────────────────
# 執行調研（使用 AI 子代理）
# ──────────────────────────────────────────────

echo "📊 開始執行銷售深度調研..."

# 創建調研目標檔
cat > "$RESEARCH_DIR/.pending-research.md" <<EOF
# 數位商品銷售深度調研任務
**觸發日期:** $TODAY
**觸發類型:** bottleneck / competitor / marketing / pricing / custom
**優先級:** high

## 當前產品狀態
- AI Prompt 庫：上架狀態待確認
- AI 實戰課程：上架狀態待確認
- 飛書模板市集：上架狀態待確認

## 待調研項目
[ ] 轉換漏斗瓶頸分析
[ ] 競品定價策略分析
[ ] 最佳行銷渠道分析
[ ] 促銷策略建議
[ ] 價格彈性分析

## 調研要求
1. 搜尋 Gumroad、LemonSqueezy 上的數位商品趨勢
2. 分析成功產品的定價、描述、行銷方式
3. 找出我們的瓶頸和改進空間
4. 給出具體、可執行的建議
5. 輸出 Markdown 報告到 research/{category}/weekly-${WEEK}.md

## 目標
- 找出阻礙銷售的最大瓶頸
- 制定 30 天行動計畫
- 預估預期收入
EOF

echo "✅ 調研目標已建立"

# 推送變更到 GitHub
cd "$REPO_DIR" || exit 1
git add -A 2>/dev/null
git commit -m "research: trigger research for $TODAY" 2>/dev/null
GIT_SSH_COMMAND="ssh -i ~/.ssh/id_ed25519_gh -o IdentitiesOnly=yes" git push origin main 2>&1 | tail -3
echo "✅ 已推送 GitHub"

echo "=== 調研觸發完成 ==="
echo ""
echo "下一步：請執行以下命令啟動 AI 調研代理："
echo "  hermes run '请執行數位商品銷售深度調研，報告存放到 research/ 目錄'"