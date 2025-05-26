import os
import re
import urllib.parse
import shutil
from datetime import datetime

# 敏感詞清單
SENSITIVE_WORDS = [
    "娱乐城", "娱乐", "体育", "电子", "真人", "电竞", "棋牌",
    "彩票", "捕鱼", "老虎机", "存款", "提款", "支付", "彩金",
    "赔率", "投注", "礼金", "博彩", "返水", "首存", "次存",
    "优惠", "佣金"
]

# 備份與日誌路徑
DOWNLOAD_DIR = os.path.expanduser("~/Downloads")
BACKUP_DIR = os.path.join(DOWNLOAD_DIR, "backup")
LOG_PATH = os.path.join(DOWNLOAD_DIR, "replace_log.txt")
log_entries = []

def encode_word(word):
    return urllib.parse.quote(word)

def find_jsp_files(base_dir):
    """尋找所有 .jsp 檔，排除 WEB-INF 資料夾"""
    jsp_files = []
    for root, dirs, files in os.walk(base_dir):
        if 'WEB-INF' in root.split(os.sep):
            continue
        for file in files:
            if file.endswith(".jsp"):
                jsp_files.append(os.path.join(root, file))
    return jsp_files

def backup_file(original_path, root_folder):
    """將原始檔案備份至 ~/Downloads/backup"""
    rel_path = os.path.relpath(original_path, root_folder)
    backup_path = os.path.join(BACKUP_DIR, rel_path)
    os.makedirs(os.path.dirname(backup_path), exist_ok=True)
    shutil.copy2(original_path, backup_path)
    return backup_path

def replace_outside_quotes(content, file_path):
    """只在非引號內容中替換敏感詞"""
    modified = False
    replacements = []

    # 將內容拆成：字串段和非字串段
    parts = re.split(r'(".*?"|\'.*?\')', content)

    for i in range(len(parts)):
        # 偶數 index：非字串部分，進行替換
        if i % 2 == 0:
            for word in SENSITIVE_WORDS:
                if word in parts[i]:
                    encoded = encode_word(word)
                    parts[i] = parts[i].replace(word, encoded)
                    replacements.append(f"{file_path} | {word} → {encoded}")
                    modified = True

    return ''.join(parts), replacements, modified

def replace_in_file(file_path, root_folder):
    """處理單一檔案"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        print(f"⚠️ 跳過非 UTF-8 編碼檔案: {file_path}")
        return False

    new_content, replacements, modified = replace_outside_quotes(content, file_path)

    if modified:
        backup_file(file_path, root_folder)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        log_entries.extend(replacements)
        print(f"✅ 替換完成：{file_path}")

    return modified

def scan_and_replace(root_folder):
    print(f"🔍 開始掃描：{root_folder}")
    jsp_files = find_jsp_files(root_folder)
    changed_files = 0

    for full_path in jsp_files:
        if replace_in_file(full_path, root_folder):
            changed_files += 1

    print(f"\n📊 掃描完成，共找到 {len(jsp_files)} 個 .jsp 檔案，修改了 {changed_files} 個")

    if log_entries:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_PATH, 'w', encoding='utf-8') as log_file:
            log_file.write(f"替換紀錄時間：{timestamp}\n\n")
            log_file.write("\n".join(log_entries))
        print(f"📝 替換詳細紀錄已儲存：{LOG_PATH}")

if __name__ == "__main__":
    import tkinter as tk
    from tkinter import filedialog

    tk.Tk().withdraw()
    target_dir = filedialog.askdirectory(title="選擇 web 資料夾（排除 WEB-INF）")

    if target_dir:
        scan_and_replace(target_dir)
    else:
        print("❌ 沒有選取任何資料夾")
