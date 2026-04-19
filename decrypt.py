import requests
import base64
import json
import re
import sys

# 加一个请求会话，设置 headers 和超时
def create_session():
    session = requests.Session()
    # 模拟浏览器请求，避免被反爬
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Connection": "keep-alive"
    })
    return session

# 通用影视仓接口解密函数（适配 ok321、肥猫 等主流加密）
def decrypt_config(text):
    try:
        # 1. 清洗文本（去空格、去换行）
        raw = text.strip().replace("\n", "").replace(" ", "")
        
        # 2. Base64 解密（影视仓最常用加密）
        try:
            decrypted = base64.b64decode(raw).decode("utf-8")
            print("✅ 成功 Base64 解密")
        except Exception as e:
            print(f"ℹ️ 不是 Base64 加密，直接解析原文本: {e}")
            decrypted = raw

        # 3. 提取合法 JSON（自动修复不规范格式）
        json_match = re.search(r"(\{.*\})", decrypted, re.DOTALL)
        if json_match:
            config_json = json_match.group(1)
            print("✅ 成功提取 JSON 片段")
            return json.loads(config_json)
        
        return json.loads(decrypted)
    except Exception as e:
        print(f"❌ 解析 JSON 失败: {e}")
        return None

def main():
    # 读取 wy.txt 中的链接
    try:
        with open("wy.txt", "r", encoding="utf-8") as f:
            urls = [line.strip() for line in f if line.strip()]
        print(f"ℹ️ 从 wy.txt 读取到 {len(urls)} 个链接")
    except Exception as e:
        print(f"❌ 读取 wy.txt 失败: {e}")
        sys.exit(1)

    if not urls:
        print("❌ wy.txt 中没有链接")
        sys.exit(1)

    session = create_session()
    # 逐个请求并解密
    final_config = None
    for url in urls:
        print(f"\n🔗 正在请求：{url}")
        try:
            # 增加超时和重试，GitHub 环境网络不稳定
            resp = session.get(url, timeout=30, allow_redirects=True)
            resp.raise_for_status()
            print(f"✅ 请求成功，状态码: {resp.status_code}")
            print(f"ℹ️ 响应内容长度: {len(resp.text)}")
            
            config = decrypt_config(resp.text)
            if config and "sites" in config:
                final_config = config
                print("✅ 解密成功，找到 sites 字段")
                break
            else:
                print("❌ 解密后未找到有效 sites 字段")
        except Exception as e:
            print(f"❌ 请求失败: {type(e).__name__}: {e}")

    # 写入 fy.json
    if final_config:
        with open("fy.json", "w", encoding="utf-8") as f:
            json.dump(final_config, f, ensure_ascii=False, indent=2)
        print("\n🎉 已成功写入 fy.json")
    else:
        print("\n❌ 所有链接都解密失败，退出")
        sys.exit(1)

if __name__ == "__main__":
    main()
