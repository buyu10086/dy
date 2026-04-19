import requests
import base64
import json
import re
import sys

# 1. 创建带请求头的会话，模拟浏览器
def create_session():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Connection": "keep-alive"
    })
    return session

# 2. 清洗文本：去除HTML标签、多余字符
def clean_text(text):
    # 去除HTML标签
    text = re.sub(r'<[^>]+>', '', text)
    # 去除多余空格、换行、制表符
    text = re.sub(r'\s+', '', text)
    # 去除非ASCII字符（避免Base64解密失败）
    text = re.sub(r'[^\x00-\x7F]+', '', text)
    return text

# 3. 通用影视仓接口解密（支持多种加密方式）
def decrypt_config(text):
    try:
        print("ℹ️ 开始解密流程...")
        # 步骤1：清洗文本
        raw = clean_text(text)
        print(f"ℹ️ 清洗后文本长度: {len(raw)}")

        # 步骤2：尝试多种Base64解密（含填充处理）
        decrypted = None
        base64_candidates = [
            raw,
            raw + '=' * ((4 - len(raw) % 4) % 4),  # 补全Base64填充符
            raw.replace('-', '+').replace('_', '/')  # URL安全Base64
        ]

        for candidate in base64_candidates:
            try:
                decrypted = base64.b64decode(candidate).decode("utf-8")
                print("✅ Base64解密成功")
                break
            except Exception as e:
                continue

        # 如果Base64解密失败，直接使用清洗后的文本
        if not decrypted:
            print("ℹ️ 不是Base64加密，使用清洗后的文本直接解析")
            decrypted = raw

        # 步骤3：提取JSON片段（适配各种不规范格式）
        json_match = re.search(r"(\{.*\})", decrypted, re.DOTALL)
        if json_match:
            config_json = json_match.group(1)
            print("✅ 成功提取JSON片段")
            return json.loads(config_json)

        # 直接解析整个文本
        return json.loads(decrypted)

    except Exception as e:
        print(f"❌ 解析JSON失败: {e}")
        return None

def main():
    # 读取wy.txt中的链接
    try:
        with open("wy.txt", "r", encoding="utf-8") as f:
            urls = [line.strip() for line in f if line.strip()]
        print(f"ℹ️ 从wy.txt读取到 {len(urls)} 个链接")
    except Exception as e:
        print(f"❌ 读取wy.txt失败: {e}")
        sys.exit(1)

    if not urls:
        print("❌ wy.txt中没有链接")
        sys.exit(1)

    session = create_session()
    final_config = None

    for url in urls:
        print(f"\n🔗 正在请求: {url}")
        try:
            # 增加超时和重定向处理
            resp = session.get(url, timeout=30, allow_redirects=True)
            resp.raise_for_status()
            print(f"✅ 请求成功，状态码: {resp.status_code}")
            print(f"ℹ️ 响应原始长度: {len(resp.text)}")

            # 解密
            config = decrypt_config(resp.text)
            if config and "sites" in config:
                final_config = config
                print("✅ 解密成功，找到有效sites字段")
                break
            else:
                print("❌ 解密后未找到有效sites字段")
        except Exception as e:
            print(f"❌ 请求失败: {type(e).__name__}: {e}")

    # 写入fy.json
    if final_config:
        with open("fy.json", "w", encoding="utf-8") as f:
            json.dump(final_config, f, ensure_ascii=False, indent=2)
        print("\n🎉 已成功写入fy.json")
    else:
        print("\n❌ 所有链接解密失败，任务退出")
        sys.exit(1)

if __name__ == "__main__":
    main()
