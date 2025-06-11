import os
import re
import tkinter as tk
from tkinter import filedialog

def find_php_post_urls(root_dir):
    php_urls = set()
    valid_extensions = {'.js', '.html', '.htm', '.jsp'}

    post_pattern = re.compile(r"\$\.post\s*\(\s*[\"']([^\"']+\.php)[\"']", re.IGNORECASE)
    ajax_pattern = re.compile(r"\$\.ajax\s*\(\s*\{\s*[^}]*?url\s*:\s*[\"']([^\"']+\.php)[\"']", re.IGNORECASE)
    fetch_pattern = re.compile(r"fetch\s*\(\s*[\"']([^\"']+\.php)[\"']\s*,\s*\{\s*[^}]*method\s*:\s*[\"']POST[\"']", re.IGNORECASE)

    for folder, _, files in os.walk(root_dir):
        for file in files:
            if os.path.splitext(file)[1] in valid_extensions:
                full_path = os.path.join(folder, file)
                try:
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()

                        matches_post = post_pattern.findall(content)
                        matches_ajax = ajax_pattern.findall(content)
                        matches_fetch = fetch_pattern.findall(content)

                        for url in matches_post + matches_ajax + matches_fetch:
                            php_urls.add(url)
                except Exception as e:
                    print(f"❌ 無法讀取：{full_path} - {e}")

    return sorted(php_urls)


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()

    target_dir = filedialog.askdirectory(title="📁 請選擇要掃描的目錄")
    if not target_dir:
        print("⚠️ 未選擇目錄，程式結束。")
        exit()

    results = find_php_post_urls(target_dir)

    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "php_post_urls.txt")
    if not results:
        print("✅ 沒有找到任何 .php 的 POST 呼叫")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("沒有找到任何 .php 的 POST 呼叫\n")
    else:
        print(f"🔍 在 {target_dir} 中找到不重複的 .php POST 呼叫：\n")
        with open(output_path, 'w', encoding='utf-8') as f:
            for url in results:
                print(f"→ {url}")
                f.write(f"{url}\n")

        print(f"\n📄 已輸出結果到：{output_path}")