import requests
import os
from datetime import datetime

# 目标URL（替换为实际返回JSON的接口）
TARGET_URLS = [
    "http://www.饭太硬.com/tv",
    "http://肥猫.com/"
]
# 保存JSON的文件名
SAVE_FILE = "ysc.json"

def fetch_json(url):
    """抓取指定URL的JSON内容"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }
    try:
        # 超时时间10秒，避免卡壳
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # 抛出HTTP错误（如404/500）
        return response.json()
    except Exception as e:
        print(f"抓取URL {url} 失败：{str(e)}")
        return None

def save_json(content, file_path):
    """保存JSON内容到文件"""
    import json
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(content, f, ensure_ascii=False, indent=2)
    print(f"JSON已保存到 {file_path}")

if __name__ == "__main__":
    # 依次尝试抓取多个URL，抓到第一个可用的即停止
    json_content = None
    for url in TARGET_URLS:
        json_content = fetch_json(url)
        if json_content:
            break
    
    if json_content:
        save_json(json_content, SAVE_FILE)
    else:
        print("所有目标URL抓取失败，终止任务")
        exit(1)  # 退出码非0，让GitHub Actions标记任务失败
