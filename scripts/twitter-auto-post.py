#!/usr/bin/env python3
"""
Twitter/X 自動推播腳本
使用 OAuth 2.0 Bearer Token 認證發送推文
"""
import json
import os
import sys
import requests
from datetime import datetime, timedelta

# 載入配置
config_path = "/home/wayne/.priv/twitter-api-config-digitalproducttw.env"
config = {}
with open(config_path) as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#"):
            if "=" in line:
                key, value = line.split("=", 1)
                config[key] = value

API_KEY = config.get("X_API_KEY", "")
API_SECRET = config.get("X_API_SECRET", "")
ACCESS_TOKEN = config.get("X_ACCESS_TOKEN", "")
REFRESH_TOKEN = config.get("X_REFRESH_TOKEN", "")
CONTENT_CALENDAR = "/home/wayne/workspace/github/ckw19810413/product-tracking/marketing-assets/twitter-x-content-calendar.json"
TWEET_SENT_FILE = "/home/wayne/workspace/github/ckw19810413/product-tracking/data/tweet-sent.json"


def refresh_bearer_token():
    """用 Client Credentials 獲取新的 Bearer Token (OAuth 2.0)"""
    import base64
    credentials = f"{API_KEY}:{API_SECRET}"
    encoded = base64.b64encode(credentials.encode()).decode()
    
    response = requests.post(
        "https://api.twitter.com/2/oauth2/token",
        headers={"Authorization": f"Basic {encoded}", "Content-Type": "application/x-www-form-urlencoded"},
        data={"grant_type": "client_credentials"},
        timeout=10
    )
    if response.status_code == 200:
        token = response.json()["access_token"]
        # Update config file with new token
        config["X_ACCESS_TOKEN"] = token
        with open(config_path) as f:
            lines = f.readlines()
        with open(config_path, "w") as f:
            for line in lines:
                if line.startswith("X_ACCESS_TOKEN="):
                    f.write(f"X_ACCESS_TOKEN={token}\n")
                else:
                    f.write(line)
        print("✅ Bearer Token 已更新")
        return token
    else:
        print(f"❌ Token 刷新失敗: {response.status_code} {response.text}")
        return None


def get_or_refresh_token():
    """獲取或刷新 Bearer Token"""
    # Try current token first
    if ACCESS_TOKEN:
        # Test if current token works
        test_resp = requests.get(
            "https://api.twitter.com/2/tweets",
            headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
            timeout=10
        )
        if test_resp.status_code in (200, 400):  # 200 ok, 400 means token valid but query error
            return ACCESS_TOKEN
    
    # Token expired, refresh
    return refresh_bearer_token()


def send_tweet(text, media_id=None):
    """發送推文"""
    token = get_or_refresh_token()
    if not token:
        print("❌ 無法獲取 Bearer Token")
        return False
    
    # 限制推文長度 (280 字元)
    if len(text) > 280:
        text = text[:277] + "..."
        print(f"⚠️ 推文截斷 (277/280 字元)")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {"text": text}
    
    try:
        response = requests.post(
            "https://api.twitter.com/2/tweets",
            json=data,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 201:
            tweet_id = response.json()["data"]["id"]
            tweet_url = f"https://x.com/status/{tweet_id}"
            print(f"✅ 推文已發布!")
            print(f"   Tweet ID: {tweet_id}")
            print(f"   URL: {tweet_url}")
            
            record_sent_tweet(text)
            return True
        elif response.status_code == 403:
            print(f"❌ 發布失敗 (403): {response.json().get('detail', 'Forbidden')}")
            return False
        else:
            print(f"❌ 發布失敗: {response.status_code}")
            print(f"   回應: {response.text[:200]}")
            return False
    
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        return False


def record_sent_tweet(text):
    """記錄已發送的推文"""
    sent = []
    if os.path.exists(TWEET_SENT_FILE):
        with open(TWEET_SENT_FILE) as f:
            try:
                data = json.load(f)
                sent = data.get("posts", [])
            except:
                pass
    
    sent.append({
        "content": text[:100],  # 只存前 100 字
        "timestamp": datetime.now().isoformat(),
        "status": "sent"
    })
    
    with open(TWEET_SENT_FILE, "w") as f:
        json.dump({
            "last_updated": datetime.now().isoformat(),
            "posts": sent
        }, f, indent=2, ensure_ascii=False)


def get_next_tweet():
    """取得下一則推文"""
    if not os.path.exists(CONTENT_CALENDAR):
        print("❌ 找不到內容日曆")
        return None
    
    with open(CONTENT_CALENDAR) as f:
        calendar = json.load(f)
    
    sent_posts = []
    if os.path.exists(TWEET_SENT_FILE):
        with open(TWEET_SENT_FILE) as f:
            try:
                data = json.load(f)
                sent_posts = data.get("posts", [])
            except:
                pass
    
    # 找出未發送的推文
    for post in calendar["posts"]:
        if post["title"] not in [s["content"][:50] for s in sent_posts]:
            return post
    
    return None


def main():
    if len(sys.argv) < 2:
        print("用法:")
        print("  python3 twitter-auto-post.py send      發送下一則推文")
        print("  python3 twitter-auto-post.py list       列出可用推文")
        print("  python3 twitter-auto-post.py sent       列出已發推文")
        print("  python3 twitter-auto-post.py refresh    刷新 Token")
        return
    
    command = sys.argv[1]
    
    if command == "send":
        tweet = get_next_tweet()
        if tweet:
            print(f"即將發送推文:")
            print("=" * 60)
            print(tweet["content"])
            print("=" * 60)
            
            # 自動發送 (cron/pipe 模式)
            auto_send = sys.stdin.isatty() is False
            confirm = "y" if auto_send else input("\n是否發送? (y/n): ")
            if confirm.lower() == "y":
                send_tweet(tweet["content"])
        else:
            print("所有推文已發送!")
    
    elif command == "list":
        if os.path.exists(CONTENT_CALENDAR):
            with open(CONTENT_CALENDAR) as f:
                calendar = json.load(f)
            
            print(f"\n可用推文 ({len(calendar['posts'])} 則):")
            for i, post in enumerate(calendar["posts"], 1):
                print(f"{i}. [{post['title']}] ({post['type']})")
        
    elif command == "sent":
        if os.path.exists(TWEET_SENT_FILE):
            with open(TWEET_SENT_FILE) as f:
                data = json.load(f)
            
            print(f"\n已發送的推文 ({len(data.get('posts', []))} 則):")
            for i, post in enumerate(data.get("posts", []), 1):
                print(f"{i}. [{post.get('timestamp', 'unknown')}] {post.get('content', '')[:80]}...")
    
    elif command == "refresh":
        refresh_bearer_token()

if __name__ == "__main__":
    main()