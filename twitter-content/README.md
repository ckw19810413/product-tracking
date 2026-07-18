# Twitter 社群管理系統

## 架構

product-tracking/
├── twitter-analytics/    # 分析與報告
├── twitter-content/      # 內容管理
├── twitter-scheduler/    # 排程系統
└── twitter-data/         # 數據儲存

## 功能

### 讀取功能（目前可用）
- 用戶資料讀取
- 粉絲數追蹤
- 推文統計
- 互動數據

### 寫入功能（待升級）
- 自動推文（需要寫入權限）
- 互動回覆（需要寫入權限）
- 自動排程（需要寫入權限）

## 使用方式

### 1. 查看帳號資料
python3 twitter-analytics/get-account-info.py

### 2. 建立分析報告
python3 twitter-analytics/generate-report.py

### 3. 管理內容日曆
python3 twitter-content/manage-calendar.py

## 下一步

1. 獲得 Twitter API 寫入權限（升級帳戶）
2. 啟用自動推文功能
3. 設定排程系統
4. 開始定期發布內容

## 內容日曆

目前包含 7 個主題：
1. 痛點共鳴
2. 預熱
3. 價值輸出
4. 上架日
5. 客戶回饋
6. 工具列表
7. 課程推廣

每個主題都有完整內容和 Hashtag 建議。