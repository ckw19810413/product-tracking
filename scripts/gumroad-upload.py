#!/usr/bin/env python3
"""
自動上傳產品到 Gumroad
需要 Gumroad Access Token
"""
import json
import os
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError
from urllib.parse import quote
import mimetypes

# ==================== 配置區 ====================
GUMROAD_ACCESS_TOKEN = ""  # ← 在此填入你的 Gumroad Access Token

BASE_DIR = Path(__file__).parent
GUMROAD_PRODUCTS_DIR = BASE_DIR.parent / "gumroad-products"
REVENUE_JSON = BASE_DIR / "data" / "revenue.json"

# 產品配置（與 gumroad-products/products/ 同步）
PRODUCTS = [
    {
        "id": "ai_prompt_library",
        "name": "繁體 AI Prompt 庫",
        "description": "高品質、經過驗證的繁體中文 AI 提示詞，100 個即拷即用",
        "price_cents": 4900,  # $49.00
        "currency": "usd",
        "file_path": GUMROAD_PRODUCTS_DIR / "products" / "prompt-library",
        "zip_path": GUMROAD_PRODUCTS_DIR / "prompt-library.zip",
        "image_path": GUMROAD_PRODUCTS_DIR / "images" / "prompt-library.png",
        "gumroad_url": "",  # 上傳後自動填入
        "status": "pending",  # pending | draft | published
    },
    {
        "id": "ai_practical_course",
        "name": "繁體中文 AI 實戰課程",
        "description": "從零到進階的 AI 應用教學，4 單元 17 堂完整課程",
        "price_cents": 29700,  # $297.00
        "currency": "usd",
        "file_path": GUMROAD_PRODUCTS_DIR / "products" / "ai-course",
        "zip_path": GUMROAD_PRODUCTS_DIR / "ai-course.zip",
        "image_path": GUMROAD_PRODUCTS_DIR / "images" / "ai-course.png",
        "gumroad_url": "",
        "status": "pending",
    },
    {
        "id": "feishu_template_marketplace",
        "name": "飛書模板市集",
        "description": "中文世界第一套專業的飛書/釘釘工作模板，13+ 套",
        "price_cents": 2900,  # $29.00
        "currency": "usd",
        "file_path": GUMROAD_PRODUCTS_DIR / "products" / "feishu-templates",
        "zip_path": GUMROAD_PRODUCTS_DIR / "feishu-templates.zip",
        "image_path": GUMROAD_PRODUCTS_DIR / "images" / "feishu-template.webp",
        "gumroad_url": "",
        "status": "pending",
    },
]

# ==================== Gumroad API ====================
def gumroad_request(method, endpoint, data=None, files=None):
    """發送 Gumroad API 請求"""
    url = f"https://api.gumroad.com/v2/{endpoint}"
    
    headers = {
        "Authorization": f"Bearer {GUMROAD_ACCESS_TOKEN}",
    }
    
    try:
        if files:
            # 需要 multipart/form-data
            import email.mime.multipart
            import email.mime.base
            import email.encoders
            import io
            
            boundary = "----WebKitFormBoundary" + os.urandom(16).hex()
            
            body = io.BytesIO()
            for key, value in (data or {}).items():
                body.write(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{key}\"\r\n\r\n{value}\r\n".encode())
            for key, file_path in files.items():
                mime_type, _ = mimetypes.guess_type(file_path)
                mime_type = mime_type or "application/octet-stream"
                with open(file_path, "rb") as f:
                    file_content = f.read()
                body.write(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{key}\"; filename=\"{os.path.basename(file_path)}\"\r\nContent-Type: {mime_type}\r\n\r\n".encode())
                body.write(file_content)
                body.write(b"\r\n")
            body.write(f"--{boundary}--\r\n".encode())
            
            request = Request(url, data=body.getvalue(), headers={**headers, "Content-Type": f"multipart/form-data; boundary={boundary}"})
        elif data:
            import urllib.parse
            body = urllib.parse.urlencode(data).encode()
            request = Request(url, data=body, headers={**headers, "Content-Type": "application/x-www-form-urlencoded"}, method=method)
        else:
            request = Request(url, headers=headers, method=method)
        
        response = urlopen(request, timeout=30)
        result = json.loads(response.read().decode())
        
        if result.get("error"):
            print(f"❌ Gumroad API 錯誤: {result['error']}")
            if "message" in result:
                print(f"   {result['message']}")
            return None
        
        return result
    
    except URLError as e:
        print(f"❌ 連線失敗: {e}")
        return None
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        return None


def upload_product(product_config):
    """上傳一個產品到 Gumroad"""
    product_id = product_config["id"]
    print(f"\n{'='*60}")
    print(f"📦 上傳產品: {product_config['name']}")
    print(f"{'='*60}")
    
    # 1. 檢查檔案是否存在
    zip_path = product_config["zip_path"]
    if not zip_path.exists():
        print(f"   ⚠️  ZIP 檔案不存在: {zip_path}")
        return None
    
    # 2. 建立產品
    print(f"   🔄 建立產品...")
    
    # 讀取描述文件
    description = product_config["description"]
    
    # 檢查是否有產品頁面 Markdown
    product_dir = product_config["file_path"]
    if product_dir.exists():
        readme = product_dir / "README.md"
        if readme.exists():
            description = readme.read_text()[:5000]
    
    result = gumroad_request("POST", "create_product", {
        "name": product_config["name"],
        "description": description,
        "price_cents": product_config["price_cents"],
        "currency": product_config["currency"],
        "purchase_message": "感謝購買！你的下載連結在下面 🎉",
        "published": product_config["status"] == "published",
        "require_shipping": False,
        "preview_content": None,  # 可放免費 preview 內容
    }, {
        "file": zip_path,
    })
    
    if not result:
        return None
    
    # 3. 上傳封面圖（如果有）
    image_path = product_config["image_path"]
    if image_path.exists():
        print(f"   🔄 上傳封面圖...")
        time.sleep(1)  # 避免 API 限制
        
        image_result = gumroad_request("POST", "update_product", {
            "product_id": result["product"]["identifier"],
            "customizable_price": 0,
            "suggested_price": None,
            "minimum_price": None,
        }, {
            "preview_image": image_path,
        })
    
    # 4. 更新本地記錄
    gumroad_url = f"https://gumroad.com/l/{result['product']['identifier']}"
    product_config["gumroad_url"] = gumroad_url
    product_config["status"] = "published" if product_config["status"] == "published" else "draft"
    
    print(f"   ✅ 產品已建立!")
    print(f"   🔗 Gumroad 連結: {gumroad_url}")
    print(f"   📝 狀態: {product_config['status']}")
    
    return result


def update_revenue_json(products):
    """更新 revenue.json"""
    data = {
        "products": {},
        "weekly_revenue": [],
        "last_updated": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    
    for p in products:
        data["products"][p["id"]] = {
            "name": p["name"],
            "gumroad_url": p["gumroad_url"],
            "lemonsqueezy_url": "",
            "price": p["price_cents"] / 100,
            "currency": p["currency"],
            "status": p["status"],
            "sales_count": 0,
            "revenue": 0,
            "notes": f"上架於 {time.strftime('%Y-%m-%d')}",
        }
    
    with open(REVENUE_JSON, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 已更新 {REVENUE_JSON}")


def main():
    if not GUMROAD_ACCESS_TOKEN:
        print("❌ 請先設定 Gumroad Access Token!")
        print("\n📖 取得方式:")
        print("   1. 登入 Gumroad: https://gumroad.com/settings/advanced")
        print("   2. 在 'Advanced Settings' 中取得 Access Token")
        print("   3. 將 Token 填入此腳本的 GUMROAD_ACCESS_TOKEN 變數")
        sys.exit(1)
    
    print(f"🚀 Gumroad 產品上傳工具")
    print(f"📦 產品總數: {len(PRODUCTS)}")
    
    # 上傳每個產品
    for product in PRODUCTS:
        upload_product(product)
        time.sleep(2)  # 避免 API 限制
    
    # 更新 revenue.json
    update_revenue_json(PRODUCTS)
    
    print(f"\n{'='*60}")
    print("✅ 所有產品已處理完畢!")
    print(f"{'='*60}")
    
    # 顯示結果摘要
    for product in PRODUCTS:
        status = "🟢 Published" if product["status"] == "published" else "🟡 Draft"
        print(f"  {status} {product['name']}: {product['gumroad_url'] or '尚未上傳'}")


if __name__ == "__main__":
    main()