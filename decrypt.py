import requests
import base64
import json
import re

# 通用影视仓接口解密函数（适配 ok321、肥猫 等主流加密）
def decrypt_config(text):
    try:
        # 1. 清洗文本（去空格、去换行）
        raw = text.strip().replace("\n", "").replace(" ", "")
        
        # 2. Base64 解密（影视仓最常用加密）
        try:
            decrypted = base64.b64decode(raw).decode("utf-8")
        except:
            decrypted = raw

        # 3. 提取合法 JSON（自动修复不规范格式）
        json_match = re.search(r"(\{.*\})", decrypted, re.DOTALL)
        if json_match:
            config_json = json_match.group(1)
            return json.loads(config_json)
        
        return json.loads(decrypted)
    except:
        return None

# 读取 wy.txt 中的链接
with open("wy.txt", "r", encoding="utf-8") as f:
    urls = [line.strip() for line in f if line.strip()]

if not urls:
    print("❌ wy.txt 中没有链接")
    exit(1)

# 逐个请求并解密
final_config = None
for url in urls:
    try:
        print(f"🔗 正在请求：{url}")
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        
        config = decrypt_config(resp.text)
        if config and "sites" in config:
            final_config = config
            print("✅ 解密成功")
            break
    except Exception as e:
        print(f"❌ 请求失败：{e}")

# 写入 fy.json
if final_config:
    with open("fy.json", "w", encoding="utf-8") as f:
        json.dump(final_config, f, ensure_ascii=False, indent=2)
    print("🎉 已成功写入 fy.json")
else:
    print("❌ 所有链接都解密失败")
