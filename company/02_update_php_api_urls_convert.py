import os

def convert_php_urls(input_file, output_file):
    if not os.path.exists(input_file):
        print(f"❌ 找不到檔案：{input_file}")
        return

    converted = []

    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            url = line.strip()
            if not url or not url.endswith(".php"):
                continue

            # 移除前綴目錄與 .php 副檔名
            filename = os.path.basename(url).replace(".php", "")
            converted_url = f"/api/{filename}"
            converted.append(converted_url)

    with open(output_file, 'w', encoding='utf-8') as f:
        for url in converted:
            print(f"✅ {url}")
            f.write(f"{url}\n")

    print(f"\n📄 已輸出轉換結果到：{output_file}")

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(current_dir, "php_post_urls.txt")
    output_path = os.path.join(current_dir, "php_post_urls_converted.txt")

    convert_php_urls(input_path, output_path)