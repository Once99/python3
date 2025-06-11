import os

def convert_php_urls(input_dir, output_file):
    if not os.path.exists(input_dir):
        print(f"❌ 找不到資料夾：{input_dir}")
        return

    urls = set()

    for filename in os.listdir(input_dir):
        if filename.endswith(".txt") and filename != output_file:
            file_path = os.path.join(input_dir, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    url = line.strip()
                    if url and (url.endswith(".php") or ".php?" in url):
                        urls.add(url)

    converted = []
    for url in sorted(urls):
        filename = os.path.basename(url).split("?")[0].replace(".php", "")
        converted_url = f"/api/{filename}"
        converted.append(converted_url)

    output_path = os.path.join(input_dir, output_file)
    with open(output_path, 'w', encoding='utf-8') as f:
        for url in converted:
            print(f"✅ {url}")
            f.write(f"{url}\n")

    print(f"\n📄 已輸出轉換結果到：{output_path}")

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(current_dir, "output")
    output_file = "php_post_urls_converted.txt"

    convert_php_urls(input_dir, output_file)