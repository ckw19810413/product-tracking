#!/usr/bin/env python3
"""
自動從內容日曆發布推文到 Twitter/X
支援 X API v2（Bearer Token 或 OAuth 1.0a）
"""
import json
import os
import sys
import time
import random
from pathlib import Path
from datetime import datetime, timedelta

# ==================== 配置區 ====================

# 選項 1: Bearer Token（只讀，不能推文）
X_BEARER_TOKEN = ""  # ← 在此填入你的 X Bearer Token

# 選項 2: OAuth 1.0a 金鑰（需要完整推文權限）
X_API_KEY = ""         # ← 在此填入你的 X API Key
X_API_SECRET = ""      # ← 在此填入你的 X API Secret
X_ACCESS_TOKEN = ""    # ← 在此填入你的 Access Token
X_ACCESS_SECRET = ""   # ← 在此填入你的 Access Token Secret

# 產品 Gumroad 連結（與 gumroad-products 同步）
PRODUCT_LINKS = {
    "prompt": "",  # 替換為實際 Gumroad 連結
    "course": "",  # 替換為實際 Gumroad 連結
    "feishu": "",  # 替換為實際 Gumroad 連結
}

# 內容日曆目錄
CONTENT_CALENDAR = Path(__file__).parent / "../marketing-assets/twitter-x-content-calendar.md"

# 追蹤已發的推文（避免重複）
SENT_FILE = Path(__file__).parent / "x_sent_tweets.json"

# 推文的帳號 (@AIWorkshopTW 或 @DigitProductTW)
TWITTER_HANDLE = "@AIWorkshopTW"

# 發送間隔（秒）
POST_INTERVAL = random.randint(300, 600)  # 5-10 分鐘
MAX_TWEETS_PER_DAY = 20  # 每日最多推文數
RATE_LIMIT_COOLDOWN = 300  # API 限制後冷靜期

# ==================== 推文內容 ====================

def get_tweet_templates():
    """內容日曆中的推文模板"""
    return [
        # Day 1: 建立痛點
        {
            "template": "你是不是也在想：\n• ChatGPT 寫的內容太生硬？\n• 寫信寫到頭昏腦脹？\n• 做簡報花一整天卻不夠好？\n\n問題不在你，是工具不對。\n\n明天分享一套「繁體中文 AI 工作流」，幫你省下 80% 時間。\n👇 追蹤我，明天見。",
            "hashtags": "#AI #繁體中文 #ChatGPT",
            "link": "",
        },
        # Day 2: 預熱
        {
            "template": "我們花了 3 個月測試 500+ prompts，\n最後只挑出 100 個真正有效的。\n\n為什麼不直接賣 500 個？\n因為品質比數量重要 100 倍。\n\n❓ 你最近用 ChatGPT 最失敗的一次經驗是什麼？\n（留言分享，我幫你想 prompt 解法）",
            "hashtags": "#Prompt #AI工具",
            "link": "",
        },
        # Day 3: 價值輸出
        {
            "template": "教你一個 ChatGPT 寫作必殺技：\n\n❌ 錯誤寫法：\n「請幫我寫一篇文章」\n\n✅ 正確寫法：\n「你是一位 [角色]。請幫我寫一篇 [主題] 的文章。\n目標受眾：[誰]。\n風格：[語氣]。\n字數：[限制]。」\n\n差異在哪？細節。\n\n明天上架一套完整 prompt 庫，包含 100 個已測試的模板。",
            "hashtags": "#ChatGPT技巧 #AI教學",
            "link": "",
        },
        # Day 4: 上架日 🚀
        {
            "template": "🎉 我們的「繁體 AI Prompt 庫」正式上線了！\n\n100 個高品質 prompt，不是廉價合集。\n涵蓋：商務、內容、效率、進階應用。\n\n💰 早鳥價：$49（約一杯手搖飲）\n📦 內含：完整 prompt 模板 + 使用指南 + 免費更新\n\n👉 立即取得：[GUMROAD_LINK]\n\n前 50 名購買者：額外贈送「社群經營 10 大 prompt」",
            "hashtags": "#AI #Prompt庫 #Gumroad",
            "link": PRODUCT_LINKS["prompt"],
        },
        # Day 5: 客戶回饋
        {
            "template": "剛剛收到第一筆購買回饋：\n\n「用了第 12 號 prompt 寫客戶郵件，回覆率提升 30%！」\n— 已購買的用戶\n\n你的下一封客戶郵件，不用自己想了。\n👉 [GUMROAD_LINK]",
            "hashtags": "#AI工具 #繁體中文",
            "link": PRODUCT_LINKS["prompt"],
        },
        # Day 6: 內容行銷
        {
            "template": "用 AI 寫社群貼文的好處：\n1. 產量快 10 倍\n2. 風格統一\n3. 不用熬夜想 caption\n4. 專注在策略，而不是打字\n\n我們有一套「社群經營 5 大 prompt」，買 Prompt 庫送。\n👉 [GUMROAD_LINK]",
            "hashtags": "#社群經營 #AI行銷",
            "link": PRODUCT_LINKS["prompt"],
        },
        # Day 7: 課程預告
        {
            "template": "這週上架了 Prompt 庫，反應不錯。\n\n下週上架「AI 實戰課程」：4 單元 17 堂，繁體中文教學。\n從零到進階，適合想系統學習的人。\n\n想先預購？留言「課程」我通知你。",
            "hashtags": "#AI實戰 #繁體中文",
            "link": "",
        },
        # 飛書模板市集推播
        {
            "template": "📋 你的團隊還在用 Excel 管專案？\n\n試試中文世界第一套專業飛書/釘釘工作模板：\n• 銷售儀表板\n• CRM 客戶管理\n• 專案甘特圖\n• 日報/週報模板\n\n💰 $29-$69/套，全部套組只要 $197\n\n👉 [GUMROAD_LINK]",
            "hashtags": "#飛書 #釘釘 #生產力",
            "link": PRODUCT_LINKS["feishu"],
        },
        # AI 實戰課程推播
        {
            "template": "想系統學習 AI？不需要懂程式！\n\n我們的「AI 實戰課程」：\n✅ 4 單元，17 堂完整課程\n✅ 繁體中文教學\n✅ 學完就能用\n\n💰 早鳥價 $297（原價 $497）\n👉 [GUMROAD_LINK]",
            "hashtags": "#AI實戰 #線上課程",
            "link": PRODUCT_LINKS["course"],
        },
        # 每週工具推薦
        {
            "template": "🔥 本週推薦 AI 工具：\n\n1. ChatGPT — 最全面的 AI 助理\n2. Midjourney — 文生圖神器\n3. Notion AI — 文件整理利器\n\n搭配我們的 Prompt 庫，效率提升 300%！\n\n👉 立即取得：[GUMROAD_LINK]",
            "hashtags": "#AITools #效率工具",
            "link": PRODUCT_LINKS["prompt"],
        },
        # 限時優惠
        {
            "template": "⏰ 限時優惠！\n\n「繁體 AI Prompt 庫」本週特売 $39（原價 $49）\n\n100 個高品質繁體中文 prompt\n涵蓋商務、內容、效率、進階應用\n\n👉 立即搶購：[GUMROAD_LINK]",
            "hashtags": "#限時優惠 #AI",
            "link": PRODUCT_LINKS["prompt"],
        },
    ]

# ==================== X/Twitter API ====================

def send_tweet_with_tweepy(text: str, media_id: str | None = None) -> bool:
    """使用 Tweepy 發送推文（如果已安裝）"""
    try:
        import tweepy
    except ImportError:
        print("⚠️  Tweepy 未安裝。執行: pip3 install tweepy")
        print("   腳本會跳過推文發送，但會記錄到 sent_tweets.json")
        record_sent_tweet(text)
        return False
    
    client = tweepy.Client(
        bearer_token=X_BEARER_TOKEN,
        consumer_key=X_API_KEY,
        consumer_secret=X_API_SECRET,
        access_token=X_ACCESS_TOKEN,
        access_token_secret=X_ACCESS_SECRET,
    )
    
    try:
        kwargs = {"text": text}
        if media_id:
            kwargs["media_ids"] = [media_id]
        
        response = client.create_tweet(**kwargs)
        tweet_id = response["id"]
        tweet_url = f"https://twitter.com/{TWITTER_HANDLE.lstrip('@')}/status/{tweet_id}"
        
        print(f"   ✅ 推文已發布!")
        print(f"   🔗 {tweet_url}")
        
        record_sent_tweet(text)
        return True
    
    except Exception as e:
        error_msg = str(e)
        print(f"   ❌ 推文發送失敗: {error_msg[:200]}")
        
        if "rate limit" in error_msg.lower() or "429" in error_msg:
            print(f"   ⏳ 觸發 Rate Limit，等待 {RATE_LIMIT_COOLDOWN}s 後重試...")
            time.sleep(RATE_LIMIT_COOLDOWN)
            return send_tweet_with_tweepy(text, media_id)
        
        record_sent_tweet(text)
        return False


def send_tweet_with_requests(text: str) -> bool:
    """使用 requests 直接呼叫 X API v2（Tweepy 不可用時）"""
    import requests
    
    # 需要 OAuth 1.0a 簽名
    try:
        from requests_oauthlib import OAuth1Session
    except ImportError:
        print("⚠️  requests-oauthlib 未安裝。執行: pip3 install requests-oauthlib")
        print("   腳本會跳過推文發送，但會記錄到 sent_tweets.json")
        record_sent_tweet(text)
        return False
    
    try:
        client = OAuth1Session(
            X_API_KEY,
            X_API_SECRET,
            X_ACCESS_TOKEN,
            X_ACCESS_SECRET,
        )
        
        response = client.post(
            "https://api.twitter.com/2/tweets",
            json={"text": text},
        )
        
        if response.status_code == 201:
            data = response.json()
            tweet_id = data["data"]["id"]
            tweet_url = f"https://twitter.com/{TWITTER_HANDLE.lstrip('@')}/status/{tweet_id}"
            
            print(f"   ✅ 推文已發布!")
            print(f"   🔗 {tweet_url}")
            
            record_sent_tweet(text)
            return True
        else:
            print(f"   ❌ 狀態碼: {response.status_code}")
            print(f"   回應: {response.text[:300]}")
            record_sent_tweet(text)
            return False
    
    except Exception as e:
        print(f"   ❌ 錯誤: {e}")
        record_sent_tweet(text)
        return False


def record_sent_tweet(text: str):
    """記錄已發送的推文"""
    sent = get_sent_tweets()
    sent.append({
        "text": text[:100],  # 只存前 100 字
        "timestamp": datetime.now().isoformat(),
    })
    with open(SENT_FILE, "w") as f:
        json.dump(sent, f, ensure_ascii=False, indent=2)


def get_sent_tweets() -> list:
    """讀取已發送的推文記錄"""
    if SENT_FILE.exists():
        with open(SENT_FILE, "r") as f:
            try:
                return json.load(f)
            except:
                return []
    return []


# ==================== 主程式 ====================

def check_credentials() -> bool:
    """檢查憑證"""
    has_oauth = all([X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET])
    has_bearer = bool(X_BEARER_TOKEN)
    
    if has_oauth:
        print("✅ OAuth 1.0a 憑證已設定")
        return True
    elif has_bearer:
        print("⚠️  只有 Bearer Token（只讀，無法推文）")
        return False
    else:
        print("❌ 沒有設定任何 Twitter API 憑證")
        print("\n📖 取得方式:")
        print("   1. 前往 https://developer.twitter.com/en/portal/dashboard")
        print("   2. 建立 Developer Account")
        print("   3. 建立 App，取得 API Key 和 Access Token")
        print("   4. 將金鑰填入此腳本的配置區")
        return False


def auto_post():
    """自動從內容日曆發推文"""
    templates = get_tweet_templates()
    
    # 過濾掉已發的
    sent = get_sent_tweets()
    available = [t for t in templates if t["template"] not in [s["text"] for s in sent]]
    
    if not available:
        print("📭 所有推文模板已發送過！")
        return
    
    # 隨機選一個（或按日期順序）
    template = available[0]  # 按順序發
    
    # 替換 GUMROAD_LINK
    for key, url in PRODUCT_LINKS.items():
        if url:
            template["template"] = template["template"].replace("[GUMROAD_LINK]", url)
    
    # 組裝推文
    tweet_text = template["template"]
    if template["hashtags"]:
        tweet_text += f"\n\n{template['hashtags']}"
    
    # 限制 280 字
    if len(tweet_text) > 280:
        tweet_text = tweet_text[:277] + "..."
    
    print(f"\n📤 即將發送推文:")
    print(f"{'='*60}")
    print(tweet_text)
    print(f"{'='*60}")
    
    # 檢查每日上限
    today_sent = len([s for s in sent if s["timestamp"].startswith(datetime.now().strftime("%Y-%m-%d"))])
    if today_sent >= MAX_TWEETS_PER_DAY:
        print(f"⚠️  今日已發送 {today_sent}/{MAX_TWEETS_PER_DAY} 則推文，達到上限")
        return
    
    print(f"\n📊 今日已發: {today_sent}/{MAX_TWEETS_PER_DAY}")
    print(f"📦 可用模板: {len(available)}")
    
    # 發送
    print(f"\n🚀 發送中...")
    success = send_tweet_with_tweepy(tweet_text) or send_tweet_with_requests(tweet_text)
    
    if success:
        print(f"\n✅ 發送成功!")
        time.sleep(POST_INTERVAL)  # 等待下一則
    else:
        print(f"\n⚠️  發送失敗，已記錄到 {SENT_FILE}")


def list_available():
    """列出所有可用的推文模板"""
    templates = get_tweet_templates()
    sent = get_sent_tweets()
    
    print(f"\n📋 可用的推文模板 ({len(templates)} 個):")
    print(f"{'='*60}")
    
    for i, t in enumerate(templates, 1):
        is_sent = t["template"] in [s["text"] for s in sent]
        status = "✅ 已發" if is_sent else "📤 待發"
        
        print(f"\n{i}. [{status}] {t['hashtags']}")
        print(f"   {t['template'][:100]}...")
    
    print(f"\n總計: {len(sent)} 已發, {len(templates) - len(sent)} 待發")


def main():
    command = sys.argv[1] if len(sys.argv) > 1 else "post"
    
    print(f"🐦 X/Twitter 自動推播工具")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    if command == "post":
        if check_credentials():
            auto_post()
        else:
            print("\n⏭️  跳過發送（沒有憑證）")
            print("   腳本會記錄要發送的推文，等你填入金鑰後再跑一次")
            # 即使沒有憑證也生成要發送的列表
            templates = get_tweet_templates()
            sent = get_sent_tweets()
            available = [t for t in templates if t["template"] not in [s["text"] for s in sent]]
            if available:
                print(f"\n📋 下次要發送的推文:")
                print(f"{'='*60}")
                print(available[0]["template"])
                print(f"{'='*60}")
    
    elif command == "list":
        list_available()
    
    elif command == "sent":
        sent = get_sent_tweets()
        print(f"\n📋 已發送的推文 ({len(sent)} 則):")
        for i, s in enumerate(sent, 1):
            print(f"{i}. [{s['timestamp']}] {s['text'][:80]}...")
    
    else:
        print(f"用法:")
        print(f"  python3 x-auto-post.py post          發送推文")
        print(f"  python3 x-auto-post.py list          列出可用模板")
        print(f"  python3 x-auto-post.py sent          列出已發推文")


if __name__ == "__main__":
    main()