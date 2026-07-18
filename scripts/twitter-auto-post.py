#!/usr/bin/env python3
"""
Twitter/X 自動推播腳本
使用 OAuth 1.0a 認證發送推文
"""
import json
import os
import sys
import requests
from datetime import datetime
from requests_oauthlib import OAuth1

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
ACCESS_SECRET = config.get("X_ACCESS_SECRET", "")
CONTENT_CALENDAR = "/home/wayne/workspace/github/ckw19810413/product-tracking/marketing-assets/twitter-x-content-calendar.json"
TWEET_SENT_FILE = "/home/wayne/workspace/github/ckw19810413/product-tracking/data/tweet-sent.json"

def send_tweet(text, media_id=None):
    """發送推文"""
    if not all([ACCESS_TOKEN, ACCESS_SECRET]):
        print("❌ 缺少 Access Token 或 Access Secret")
        return False
    
    # OAuth 1.0a 認證
    oauth = OAuth1(
        API_KEY,
        api_secret=API_SECRET,
        resource_owner_key=ACCESS_TOKEN,
        resource_owner_secret=ACCESS_SECRET
    )
    
    # 準備推文資料
    data = {"text": text}
    if media_id:
        data["media_ids"] = [media_id]
    
    try:
        response = requests.post(
            "https://api.twitter.com/2/tweets",
            json=data,
            auth=oauth
        )
        
        if response.status_code == 201:
            tweet_id = response.json()["data"]["id"]
            tweet_url = f"https://twitter.com/hashtag/AI/status/{tweet_id}"
            print(f"✅ 推文已發布!")
            print(f"   Tweet ID: {tweet_id}")
            print(f"   URL: {tweet_url}")
            
            # 記錄已發送的推文
            record_sent_tweet(text)
            return True
        else:
            print(f"❌ 發布失敗: {response.status_code}")
            print(f"   回應: {response.text}")
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
        return
    
    command = sys.argv[1]
    
    if command == "send":
        tweet = get_next_tweet()
        if tweet:
            print(f"即將發送推文:")
            print("="*60)
            print(tweet["content"])
            print("="*60)
            
            # 確認發送
            confirm = input("\n是否發送? (y/n): ")
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

if __name__ == "__main__":
    main()
