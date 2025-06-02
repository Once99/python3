import os
import re
import urllib.parse
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SENSITIVE_WORDS_PATH = os.path.join(SCRIPT_DIR, "sensitive_words.txt")
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

def find_all_files(project_root):
    target_dir = os.path.join(project_root, "src", "pages")
    all_files = []
    for root, dirs, files in os.walk(target_dir):
        for file in files:
            if file == ".DS_Store":
                continue
            full_path = os.path.join(root, file)
            all_files.append(full_path)
    return all_files

def replace_in_template_tagged_html(content, file_path, sensitive_words):
    modified = False
    replacements = []

    def replace_inside_template(template_match):
        block = template_match.group(0)

        def replace_tag_content(match):
            tag_name, attrs, inner = match.groups()
            for word in sensitive_words:
                if word in inner:
                    encoded = encode_word(word)
                    inner = inner.replace(word, encoded)
                    replacements.append(f"{file_path} | <{tag_name}> {word} → {encoded}")
                    nonlocal modified
                    modified = True
            return f"<{tag_name}{attrs}>{inner}</{tag_name}>"

        tag_pattern = re.compile(r"<(\w+)([^<>]*?)>([^<>]+?)</\1>", re.DOTALL)
        return tag_pattern.sub(replace_tag_content, block)

    content_new = re.sub(r"<template[\s\S]*?</template>", replace_inside_template, content, flags=re.IGNORECASE)
    return content_new, replacements, modified

def replace_in_file(file_path, root_folder, sensitive_words):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        print(f"⚠️ 跳過非 UTF-8 編碼檔案: {file_path}")
        return False

    new_content, replacements, modified = replace_in_template_tagged_html(content, file_path, sensitive_words)

    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        log_entries.extend(replacements)
        print(f"✅ 替換完成：{file_path}")

    return modified

def scan_and_replace(project_root, sensitive_words):
    print(f"🔍 開始掃描：{os.path.join(project_root, 'src/pages')}")
    all_files = find_all_files(project_root)
    changed_files = 0

    for full_path in all_files:
        if replace_in_file(full_path, project_root, sensitive_words):
            changed_files += 1

    print(f"\n📊 掃描完成，共找到 {len(all_files)} 個檔案，修改了 {changed_files} 個")

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
    project_root = filedialog.askdirectory(title="選擇專案根目錄（包含 src/pages）")
    sensitive_words = load_sensitive_words(SENSITIVE_WORDS_PATH)

    if project_root and sensitive_words:
        scan_and_replace(project_root, sensitive_words)
    elif not project_root:
        print("❌ 沒有選取任何資料夾")
