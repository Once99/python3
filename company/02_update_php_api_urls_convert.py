import os

def convert_php_urls(input_dir, output_file):
    if not os.path.exists(input_dir):
        print(f"❌ 找不到資料夾：{input_dir}")
        return

    urls = {}

    for filename in os.listdir(input_dir):
        if filename.endswith(".txt") and filename != output_file:
            file_path = os.path.join(input_dir, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    url = line.strip()
                    if url and (url.endswith(".php") or ".php?" in url):
                        if url not in urls:
                            urls[url] = filename  # 儲存來源檔名

    converted_set = set()
    converted = []
    for url in sorted(urls):
        base_name = os.path.basename(url).split("?")[0].replace(".php", "")
        converted_url = f"/api/{base_name}"
        if converted_url not in converted_set:
            comment = f"# from: {urls[url]}"
            converted.append((converted_url, comment))
            converted_set.add(converted_url)

    output_path = os.path.join(input_dir, output_file)
    with open(output_path, 'w', encoding='utf-8') as f:
        for url, comment in converted:
            print(f"✅ {url} {comment}")
            f.write(f"{url} {comment}\n")

    print(f"\n📄 已輸出轉換結果到：{output_path}")

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(current_dir, "output")
    output_file = "all_php_api_converted.txt"

    convert_php_urls(input_dir, output_file)