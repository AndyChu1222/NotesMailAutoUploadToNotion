import os
import re
import json
import hashlib
from datetime import datetime
import requests
from dotenv import load_dotenv
import chardet
import pandas as pd

print("✅ 正在執行最新版本...")

# 載入 .env 設定
load_dotenv()
EXPORT_PATH = os.getenv("EXPORT_PATH")
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("DATABASE_ID")

print("✅ EXPORT_PATH:", EXPORT_PATH)
print("✅ DATABASE_ID:", DATABASE_ID)
print("✅ NOTION_TOKEN 長度:", len(NOTION_TOKEN) if NOTION_TOKEN else "未讀取")

if not all([EXPORT_PATH, NOTION_TOKEN, DATABASE_ID]):
    raise ValueError("❌ 請確認 .env 中的設定")

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

# 擷取資料夾資訊
def extract_info_from_folder(folder_name):
    title_match = re.search(r"\[Crash\].*?\[V(?P<version>[\d\.]+)\]", folder_name)
    version = title_match.group("version") if title_match else "Unknown"
    date_match = re.search(r"_(\d{8})_(\d{6})", folder_name)
    if date_match:
        date_str = date_match.group(1)
        date_obj = datetime.strptime(date_str, "%Y%m%d")
        # 為了切割最後兩個字串元素
        folder_name,_ = folder_name.rsplit("_",1)
        folder_name,_ = folder_name.rsplit("_",1)
        return {
            "title": folder_name,
            "version": version,
            "date": date_obj.strftime("%Y-%m-%d")
        }
    return None

# 擷取分隔線後內容
def extract_body_after_separator(content, separator="="):
    lines = content.splitlines()
    for idx, line in enumerate(lines):
        if separator * 10 in line:
            return "\n".join(lines[idx + 1:])
    return content

# 切割超過 2000 字的段落
def split_text_to_blocks(content, max_len=2000):
    blocks = []
    for i in range(0, len(content), max_len):
        chunk = content[i:i + max_len]
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{
                    "type": "text",
                    "text": {"content": chunk}
                }]
            }
        })
    return blocks

# 自動讀取並偵測編碼
def read_file_auto_encoding(file_path):
    with open(file_path, 'rb') as f:
        raw = f.read()
        result = chardet.detect(raw)
        encoding = result['encoding'] or 'utf-8'
    return raw.decode(encoding, errors="replace")

# 建立 Page 至 Notion
def create_notion_page(info, content):
    payload = {
        "parent": {"database_id": DATABASE_ID},
        "properties": {
            "Name": {"title": [{"text": {"content": info["title"]}}]},
            "Date": {"date": {"start": info["date"]}},
            "Status": {"status": {"name": "Not started"}},
            "Version": {"select": {"name": info["version"]}},
            "Files": {"files": []}
        },
        "children": split_text_to_blocks(content)
    }
    res = requests.post("https://api.notion.com/v1/pages", headers=HEADERS, json=payload)
    return res.status_code, res.text

# 計算雜湊
def compute_content_hash(content):
    return hashlib.sha256(content.encode("utf-8")).hexdigest()

# 載入與儲存雜湊紀錄
def load_uploaded_hashes(file_path="uploaded_hashes.txt"):
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="Big5") as f:
            return set(line.strip() for line in f.readlines())
    return set()

def save_uploaded_hash(hash_value, file_path="uploaded_hashes.txt"):
    with open(file_path, "a", encoding="Big5") as f:
        f.write(hash_value + "\n")

# 主流程
results = []
uploaded_hashes = load_uploaded_hashes()

if os.path.exists(EXPORT_PATH):
    for folder in os.listdir(EXPORT_PATH):
        folder_path = os.path.join(EXPORT_PATH, folder)
        if os.path.isdir(folder_path):
            content_file = os.path.join(folder_path, "content.txt")
            if os.path.exists(content_file):
                raw = read_file_auto_encoding(content_file)
                content = extract_body_after_separator(raw)
                content_hash = compute_content_hash(content)

                if content_hash in uploaded_hashes:
                    print(f"⏩ 跳過重複資料夾：{folder}")
                    continue

                info = extract_info_from_folder(folder)
                if info:
                    status, msg = create_notion_page(info, content)
                    if status == 200:
                        save_uploaded_hash(content_hash)
                    results.append((folder, status, msg))

# 匯出結果
df = pd.DataFrame(results, columns=["資料夾", "狀態碼", "訊息"])
df.to_csv("notion_upload_result.csv", index=False, encoding="utf-8-sig")
print("📄 結果已匯出為 notion_upload_result.csv")
