# 數位商品「零到第一筆銷售」上架檢查清單

> 完成所有勾選項目後，你的產品就會開始產生收入。

---

## ✅ 上架前準備（Day 1）

- [ ] 建立 Gumroad 帳號（gumroad.com/signup）
- [ ] 完成 KYC 金流設定（Payoneer / 銀行帳號）
- [ ] 確認帳號驗證 email
- [ ] 準備產品檔案（PDF / Markdown / ZIP）

---

## ✅ 產品上架（Day 2-3）

### Prompt 庫
- [ ] 上傳檔案（`prompts/` 目錄的 4 個 .md 文件）
- [ ] 標題：`繁體 AI Prompt 庫 — 100 個高品質繁體中文 AI 提示詞，即拷即用`
- [ ] 描述：使用 `research/promotional-strategies/gumroad-upload-guide.md` 的完整文案
- [ ] 設定價格：$49 USD
- [ ] 上傳封面圖（建議 1200×628 像素，科技藍色系）
- [ ] 標籤：`ai` `prompt` `chatgpt` `productivity` `繁體中文` `templates`
- [ ] 設定免費預覽（貼上 5 個範例 prompt）
- [ ] 點擊 Publish

### AI 實戰課程
- [ ] 上傳內容大綱 + 完整課程文件
- [ ] 標題：`繁體中文 AI 實戰課程 — 4 單元 17 堂，從零到進階`
- [ ] 描述：使用 Gumroad 上傳指南的完整文案
- [ ] 設定價格：$297 USD（早鳥）
- [ ] 上傳封面圖（紫色系，科技感）
- [ ] 標籤：`ai` `course` `tutorial` `prompt` `繁體中文` `learning`
- [ ] 設定免費預覽（第 1 堂前 5 分鐘內容）
- [ ] 點擊 Publish

### 飛書模板市集
- [ ] 上傳模板文件（可先放銷售儀表板範本）
- [ ] 標題：`飛書模板市集 — 中文世界第一套專業的飛書/釘釘工作模板`
- [ ] 描述：使用 Gumroad 上傳指南的完整文案
- [ ] 設定價格：$29 USD（單套）/ $197 USD（全部套組）
- [ ] 上傳封面圖（藍色系，專業感）
- [ ] 標籤：`feishu` `lark` `template` `notion` `productivity` `project-management`
- [ ] 設定免費預覽（銷售儀表板範本）
- [ ] 點擊 Publish

---

## ✅ 連結紀錄與 Landing Page 更新（Day 4）

- [ ] 複製 Prompt 庫 Gumroad 連結，寫入 `data/gumroad-urls.txt`
- [ ] 複製 AI 課程 Gumroad 連結，寫入 `data/gumroad-urls.txt`
- [ ] 複製飛書模板 Gumroad 連結，寫入 `data/gumroad-urls.txt`
- [ ] 更新 Landing Page `src/app/page.tsx` 的 CTA 按鈕連結
- [ ] 執行 `pnpm build` 確認無錯誤
- [ ] 部署到 Vercel（`vercel deploy` 或手動部署）

---

## ✅ 行銷啟動（Day 5-7）

### Twitter/X
- [ ] 建立帳號 @AIWorkshopTW（或自訂）
- [ ] 更新簡介：「幫繁體中文用戶用 AI 提升 10 倍效率 | 創作者 | 產品：[Gumroad 連結]」
- [ ] 發布 Day 1 推文（痛點 + 預熱）
- [ ] 追蹤 20+ 同領域創作者，互動他們的推文

### Reddit
- [ ] 用同一個帳號註冊
- [ ] 發布 r/chatgpt 帖子（使用模板 A）
- [ ] 發布 r/productivity 帖子
- [ ] 發布 r/SaaS 帖子（上架後）
- [ ] 回覆所有留言（增加互動率）

### Landing Page
- [ ] 確保所有 CTA 按鈕連到正確 Gumroad 連結
- [ ] 確認頁面載入速度 < 3 秒
- [ ] 手機/桌機測試顯示正常

---

## ✅ 上架後追蹤（Day 8-30）

- [ ] 每天檢查 Gumroad Dashboard（銷售、點擊、退款）
- [ ] 每週一 10:00 AM 自動生成報告（cron job 已設定）
- [ ] 收集早期客戶反饋
- [ ] 每週更新 1 則 Twitter 內容
- [ ] 每週在 Reddit 發 1-2 則新文
- [ ] 每月更新 `research/bottlenecks/` 調研報告

---

## 💰 預期收入時間軸

| 時間 | 狀態 | 預估月收入 |
|------|------|-----------|
| Day 1-7 | 剛上架，冷啟動 | $0-$200 |
| Week 2-3 | 行銷生效 | $200-$800 |
| Month 2 | 累積口碑 | $500-$2,000 |
| Month 3+ | 穩定增長 | $1,000-$5,000+ |

---

## 🚨 瓶頸觸發條件

完成以下任一項時，自動觸發深度調研：
- 上架後 7 天無銷售 → 檢查 Landing Page 轉換率
- 上架後 14 天無銷售 → 啟動「價格調整調研」
- 上架後 30 天收入 < $100 → 啟動「全盤行銷策略調研」

所有調研報告自動存放到 `research/bottlenecks/` 並推送到 GitHub。

---
*完成所有勾選後，你的數位商品事業就正式啟動了！*