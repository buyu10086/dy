import requests
import base64
import json
import re
import sys
import urllib.parse

def install_demjson():
    """自动安装demjson3库"""
    try:
        import demjson3
        return True
    except ImportError:
        import subprocess
        import pip
        subprocess.check_call([sys.executable, "-m", "pip", "install", "demjson3"])
        return True

# 安装并导入demjson
install_demjson()
import demjson3

def create_session():
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Connection": "keep-alive"
    })
    return session

def clean_text(text):
    """清洗文本，去除HTML标签、多余空格和BOM头"""
    # 去除UTF-8 BOM头
    text = text.lstrip('\ufeff')
    # 去除HTML标签
    text = re.sub(r'<[^>]+>', '', text)
    # 去除多余空格、换行和制表符
    text = re.sub(r'\s+', '', text)
    return text

def decode_url_safe_base64(s):
    """处理URL安全的Base64"""
    s = s.replace('-', '+').replace('_', '/')
    s += '=' * ((4 - len(s) % 4) % 4)
    try:
        return base64.b64decode(s).decode("utf-8")
    except:
        return None

def try_all_decoders(text):
    """尝试所有可能的解码方式"""
    decoders = [
        ("原始文本", lambda t: t),
        ("URL解码", lambda t: urllib.parse.unquote(t)),
        ("URL解码两次", lambda t: urllib.parse.unquote(urllib.parse.unquote(t))),
        ("Base64", lambda t: base64.b64decode(t).decode("utf-8") if len(t) > 0 else None),
        ("URL安全Base64", decode_url_safe_base64),
        ("Base64+URL解码", lambda t: base64.b64decode(urllib.parse.unquote(t)).decode("utf-8") if len(t) > 0 else None),
    ]

    for name, decoder in decoders:
        try:
            result = decoder(text)
            if result:
                print(f"✅ 尝试 {name} 成功")
                return result
        except Exception as e:
            continue
    return None

def extract_and_parse_json(text):
    """从文本中提取并解析JSON，支持不规范格式"""
    # 1. 先匹配所有可能的JSON片段
    matches = re.findall(r'(\{.*\})', text, re.DOTALL)
    if not matches:
        print("❌ 未找到JSON片段")
        return None

    # 2. 尝试解析每个JSON片段（优先最长的）
    for json_str in sorted(matches, key=len, reverse=True):
        try:
            # 使用demjson解析不规范JSON
            config = demjson3.decode(json_str)
            if isinstance(config, dict) and "sites" in config:
                print("✅ 成功解析不规范JSON")
                return config
        except Exception as e:
            continue

    print("❌ 所有JSON片段解析失败")
    return None

def decrypt_config(raw_text):
    try:
        # 1. 保存原始内容到调试文件
        with open("debug_original.txt", "w", encoding="utf-8") as f:
            f.write(raw_text)
        print("ℹ️ 已保存原始响应到 debug_original.txt")

        # 2. 清洗文本
        cleaned = clean_text(raw_text)
        print(f"ℹ️ 清洗后文本长度: {len(cleaned)}")

        # 3. 尝试所有解码方式
        decoded = try_all_decoders(cleaned)
        if not decoded:
            print("❌ 所有解码方式都失败")
            return None

        # 4. 提取并解析JSON
        config = extract_and_parse_json(decoded)
        return config

    except Exception as e:
        print(f"❌ 解密过程出错: {e}")
        return None

def main():
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
            resp = session.get(url, timeout=30, allow_redirects=True)
            resp.raise_for_status()
            print(f"✅ 请求成功，状态码: {resp.status_code}")
            print(f"ℹ️ 响应原始长度: {len(resp.text)}")

            config = decrypt_config(resp.text)
            if config:
                final_config = config
                print("✅ 解密成功！")
                break
        except Exception as e:
            print(f"❌ 请求失败: {type(e).__name__}: {e}")

    if final_config:
        with open("fy.json", "w", encoding="utf-8") as f:
            json.dump(final_config, f, ensure_ascii=False, indent=2)
        print("\n🎉 已成功写入fy.json")
    else:
        print("\n❌ 所有链接解密失败，请检查debug_original.txt文件")
        sys.exit(1)

if __name__ == "__main__":
    main()
