#!/bin/bash
# 數位商品每週追蹤 & GitHub 推送
# 由 cron job 自動執行

REPO_DIR="/home/wayne/workspace/hermes-agent/projects/product-tracking"
REPORT_DIR="$REPO_DIR/reports"
DATA_DIR="$REPO_DIR/data"
SCRIPT_DIR="/home/wayne/workspace/hermes-agent/projects/product-tracking/scripts"

echo "=== 數位商品每週追蹤開始 ==="

# 1. 讀取追蹤數據
TRACKER="$DATA_DIR/README.md"
if [ ! -f "$TRACKER" ]; then
    echo "ERROR: 追蹤數據檔不存在"
    exit 1
fi

# 2. 生成每週報告
WEEK=$(date +%G-W%V)
REPORT_FILE="$REPORT_DIR/weekly-${WEEK}.md"
TODAY=$(date +%Y-%m-%d)

echo "# 數位商品每週收入報告
## ${WEEK} (${TODAY})
**報告日期:** \$(date '+%Y-%m-%d')
**生成時間:** \$(date '+%H:%M:%S')

### 財務摘要
| 指標 | 數值 |
|------|------|
| 總收入 | \$0.00（待上架） |
| 新增客戶 | 0 |

### 產品狀態
- **AI Prompt 庫** - Gumroad/LemonSqueezy 上架狀態待確認
- **AI 實戰課程** - 上架狀態待確認
- **飛書模板市集** - 上架狀態待確認

### 本週進度
(待記錄)

### 下週目標
- [ ] 確認產品上架狀態
- [ ] 啟動行銷渠道

---
*每週一 10:00 AM 自動生成*" > "$REPORT_FILE"

echo "報告已生成: $REPORT_FILE"

# 3. 推送變更到 GitHub
cd /home/wayne/workspace/hermes-agent/projects/product-tracking || exit 1

# 確保有 remote
if ! git remote get-url origin &>/dev/null; then
    git remote add origin git@github.com:ckw19810413/product-tracking.git 2>/dev/null || true
fi

# 如果有新報告或更新檔，提交並推送
if git status --porcelain | grep -q "product-tracking"; then
    git add -A
    git commit -m "chore: weekly report ${WEEK} - $(date '+%Y-%m-%d')" 2>/dev/null
    GIT_SSH_COMMAND="ssh -i ~/.ssh/id_ed25519_gh -o IdentitiesOnly=yes" git push origin main 2>&1 | tail -3
    echo "已推送變更到 GitHub"
else
    echo "無變更需要推送"
fi

echo "=== 數位商品每週追蹤結束 ==="