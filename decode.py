import base64

# 影视仓通用解密（饭太硬/肥猫/大部分仓通用）
def decode_cang_url(encrypted_text):
    try:
        s = encrypted_text.strip()
        s = s.replace("_", "/").replace("-", "+")
        missing_padding = len(s) % 4
        if missing_padding:
            s += "=" * (4 - missing_padding)
        decrypted = base64.b64decode(s).decode("utf-8")
        return decrypted.strip()
    except:
        return None

# ================== 主逻辑 ==================
if __name__ == "__main__":
    # 1. 读取 wy.txt 里的接口
    with open("wy.txt", "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    # 2. 解密所有接口
    decoded_urls = []
    for line in lines:
        res = decode_cang_url(line)
        if res:
            decoded_urls.append(res)

    # 3. 生成标准订阅格式（直接写入 fy.json）
    json_content = "{"
    json_content += '"urls":['
    json_content += ",".join(f'"{url}"' for url in decoded_urls)
    json_content += "]}"

    # 4. 覆盖保存到 fy.json（订阅用）
    with open("fy.json", "w", encoding="utf-8") as f:
        f.write(json_content)

    # 同时保存一份可读版
    with open("decoded_result.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(decoded_urls))

    print(f"✅ 解密完成！共 {len(decoded_urls)} 个接口，已覆盖到 fy.json")
