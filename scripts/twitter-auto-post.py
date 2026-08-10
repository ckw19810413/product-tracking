#!/usr/bin/env python3
"""
Twitter/X 自動推播腳本
使用 OAuth 1.0a 認證發送推文 (@KWC59125740, read/write)

2026-08-04 修復: 原腳本載入 digitalproducttw.env (OAuth 2.0 app-only,
只讀, 且 @DigitalProduct 帳號已被暫停), 導致 POST /2/tweets 403。
改用 twitter-api-config.sh 的 OAuth 1.0a 憑證 (可讀寫)。
"""
import json
import os
import sys
import requests
from datetime import datetime

# 載入配置 (OAuth 1.0a — @KWC59125740, read/write)
config_path = "/home/wayne/.priv/twitter-api-config.sh"
config = {}
with open(config_path) as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#"):
            if "=" in line:
                key, value = line.split("=", 1)
                config[key] = value.strip('"').strip("'")

API_KEY = config.get("X_API_KEY", "")
API_SECRET = config.get("X_API_SECRET", "")
ACCESS_TOKEN = config.get("X_ACCESS_TOKEN", "")
ACCESS_SECRET = config.get("X_ACCESS_SECRET") or config.get("X_ACCESS_TOKEN_SECRET", "")
CONTENT_CALENDAR = "/home/wayne/workspace/github/ckw19810413/product-tracking/marketing-assets/twitter-x-content-calendar.json"
TWEET_SENT_FILE = "/home/wayne/workspace/github/ckw19810413/product-tracking/data/tweet-sent.json"

# 若 OAuth 1.0a 憑證不完整, 改用 xurl (已配置 oauth1) 作為備援
XURL_FALLBACK = bool(API_KEY and API_SECRET and ACCESS_TOKEN and ACCESS_SECRET) is False


def send_tweet(text, media_id=None):
    """發送推文 (OAuth 1.0a user context — read/write)"""
    # 限制推文長度 (280 字元)
    if len(text) > 280:
        text = text[:277] + "..."
        print(f"⚠️ 推文截斷 (277/280 字元)")

    try:
        from requests_oauthlib import OAuth1Session
        client = OAuth1Session(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET)
        response = client.post(
            "https://api.twitter.com/2/tweets",
            json={"text": text},
            timeout=30,
        )
    except Exception as e:
        print(f"❌ OAuth1 發送錯誤: {e}")
        return False

    if response.status_code == 201:
        tweet_id = response.json()["data"]["id"]
        tweet_url = f"https://x.com/status/{tweet_id}"
        print(f"✅ 推文已發布!")
        print(f"   Tweet ID: {tweet_id}")
        print(f"   URL: {tweet_url}")
        record_sent_tweet(text)
        return True
    elif response.status_code == 403:
        body = response.text
        if "duplicate" in body.lower():
            # Duplicate content — mark as sent to prevent future loops
            print(f"❌ 發布失敗 (403 duplicate): {body[:200]}")
            print(f"   ⚠️ 已標記為 sent (防止重複嘗試)")
            record_sent_tweet(text)
        else:
            # Other 403 (e.g. account restricted / not permitted) — do NOT mark
            # as sent, otherwise the tweet is silently dropped without posting.
            print(f"❌ 發布失敗 (403): {body[:200]}")
            print(f"   ⚠️ 未標記為 sent (保留待重試)")
        return False
    elif response.status_code == 401:
        print(f"❌ 發布失敗 (401 auth): {response.text[:200]}")
        return False
    else:
        print(f"❌ 發布失敗: {response.status_code}")
        print(f"   回應: {response.text[:200]}")
        return False


def send_tweet_via_xurl(text):
    """備援: 透過 xurl CLI (OAuth 1.0a app=slashman413) 發送"""
    import subprocess
    try:
        r = subprocess.run(
            ["xurl", "post", "--app", "slashman413", text],
            capture_output=True, text=True, timeout=60,
        )
    except Exception as e:
        print(f"❌ xurl 錯誤: {e}")
        return False
    if r.returncode == 0:
        try:
            tweet_id = json.loads(r.stdout)["data"]["id"]
        except Exception:
            tweet_id = "unknown"
        print(f"✅ 推文已發布 (via xurl)!")
        print(f"   Tweet ID: {tweet_id}")
        print(f"   URL: https://x.com/status/{tweet_id}")
        record_sent_tweet(text)
        return True
    print(f"❌ xurl 發布失敗: {(r.stderr or r.stdout)[:200]}")
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

    # 找出未發送的推文 — 比對完整內容 (content[:80] 覆蓋 title 比對的不準確性)
    for post in calendar["posts"]:
        post_preview = post["content"][:80]
        already_sent = any(
            sent_content[:80] == post_preview or sent_content[:50] == post["content"][:50]
            for sent_content in [s["content"] for s in sent_posts]
        )
        if not already_sent:
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


if __name__ == "__main__":
    main()
