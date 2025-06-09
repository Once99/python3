import os
import re
import urllib.parse
from datetime import datetime

# 取得腳本所在目錄
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SENSITIVE_WORDS_PATH = os.path.join(SCRIPT_DIR, "sensitive_words.txt")

# 日誌路徑
DOWNLOAD_DIR = os.path.expanduser("~/Downloads")
LOG_PATH = os.path.join(DOWNLOAD_DIR, "replace_log.txt")
log_entries = []

def load_sensitive_words(path):
    if not os.path.exists(path):
        print(f"⚠️ 找不到敏感詞清單：{path}")
        return []
    with open(path, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

def encode_word(word):
    return ''.join(f'&#{ord(c)};' for c in word)

def find_jsp_files(base_dir):
    """尋找所有 .jsp 檔"""
    jsp_files = []
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith(".jsp"):
                jsp_files.append(os.path.join(root, file))
    return jsp_files

def replace_outside_quotes(content, file_path, sensitive_words):
    """只在非引號內容中替換敏感詞"""
    modified = False
    replacements = []
    parts = re.split(r'(".*?"|\'.*?\')', content)

    for i in range(len(parts)):
        if i % 2 == 0:  # 非字串部分
            for word in sensitive_words:
                if word in parts[i]:
                    encoded = encode_word(word)
                    parts[i] = parts[i].replace(word, encoded)
                    replacements.append(f"{file_path} | {word} → {encoded}")
                    modified = True
    return ''.join(parts), replacements, modified

def replace_in_file(file_path, root_folder, sensitive_words):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        print(f"⚠️ 跳過非 UTF-8 編碼檔案: {file_path}")
        return False

    new_content, replacements, modified = replace_outside_quotes(content, file_path, sensitive_words)

    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        log_entries.extend(replacements)
        print(f"✅ 替換完成：{file_path}")

    return modified

def scan_and_replace(root_folder, sensitive_words):
    print(f"🔍 開始掃描：{root_folder}")
    jsp_files = find_jsp_files(root_folder)
    changed_files = 0

    for full_path in jsp_files:
        if replace_in_file(full_path, root_folder, sensitive_words):
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
    target_dir = filedialog.askdirectory(title="選擇 WebRoot 資料夾（排除 WEB-INF）")
    sensitive_words = load_sensitive_words(SENSITIVE_WORDS_PATH)

    if target_dir and sensitive_words:
        scan_and_replace(target_dir, sensitive_words)
    elif not target_dir:
        print("❌ 沒有選取任何資料夾")
