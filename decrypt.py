import requests
import base64
import json
import re
import sys
import urllib.parse

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
    # 去除非ASCII字符（避免Base64解码失败）
    text = re.sub(r'[^\x00-\x7F]+', '', text)
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
                # 保存解码后的文本，方便调试
                with open(f"debug_decoded_{name}.txt", "w", encoding="utf-8") as f:
                    f.write(result)
                return result
        except Exception as e:
            print(f"❌ 尝试 {name} 失败: {e}")
            continue
    return None

def fix_json_format(json_str):
    """彻底修复不规范JSON格式"""
    # 1. 去除JSON前后的非JSON字符（包括换行、空格、非ASCII）
    json_str = re.sub(r'^[^{]*', '', json_str)
    json_str = re.sub(r'[^}]*$', '', json_str)
    
    # 2. 单引号转双引号（处理所有未转义的单引号）
    json_str = re.sub(r"(?<!\\)'", '"', json_str)
    
    # 3. 修复末尾多余的逗号
    json_str = re.sub(r',\s*([}\]])', r'\1', json_str)
    
    # 4. 修复不规范的转义（比如多个反斜杠）
    json_str = json_str.replace('\\\\', '\\')
    
    # 5. 修复不规范的数字/字符串格式（比如key没有引号）
    json_str = re.sub(r'(\w+)\s*:', r'"\1":', json_str)
    
    return json_str

def extract_json(text):
    """从文本中提取并修复JSON片段"""
    # 匹配最外层的{}结构（尽可能匹配最大的JSON对象）
    matches = re.findall(r'(\{.*\})', text, re.DOTALL)
    if matches:
        # 取最长的那个JSON片段（大概率是完整配置）
        longest_json = max(matches, key=len)
        # 修复不规范的JSON格式
        fixed_json = fix_json_format(longest_json)
        return fixed_json
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
        with open("debug_cleaned.txt", "w", encoding="utf-8") as f:
            f.write(cleaned)

        # 3. 尝试所有解码方式
        decoded = try_all_decoders(cleaned)
        if not decoded:
            print("❌ 所有解码方式都失败")
            return None

        # 4. 从解码结果中提取并修复JSON
        json_str = extract_json(decoded)
        if not json_str:
            print("❌ 未找到JSON片段")
            return None
        print("ℹ️ 已提取并修复JSON片段")
        with open("debug_fixed_json.txt", "w", encoding="utf-8") as f:
            f.write(json_str)

        # 5. 解析修复后的JSON
        config = json.loads(json_str)
        if "sites" in config:
            return config
        else:
            print("❌ JSON中没有sites字段")
            return None

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
        print("\n❌ 所有链接解密失败，请检查仓库中的debug_*.txt文件")
        sys.exit(1)

if __name__ == "__main__":
    main()
