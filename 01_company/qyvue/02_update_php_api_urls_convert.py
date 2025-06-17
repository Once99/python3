import os

def merge_all_txt_in_output(output_dir="output", merged_filename="merged_api_all.txt"):
    merged_path = os.path.join(output_dir, merged_filename)
    seen_api_urls = set()  # 用來記錄已出現過的 API 地址

    with open(merged_path, 'w', encoding='utf-8') as outfile:
        for fname in sorted(os.listdir(output_dir)):
            if fname.endswith('.txt') and fname != merged_filename:
                file_path = os.path.join(output_dir, fname)
                with open(file_path, 'r', encoding='utf-8') as infile:
                    current_block = []
                    api_url = None

                    for line in infile:
                        if line.startswith("1.訪問頁面："):
                            current_block = [line]
                            api_url = None  # 重置
                        elif line.startswith("2.API地址："):
                            api_url = line.strip()
                            current_block.append(line)
                        elif line.strip() == "--------------------------------------------------":
                            current_block.append(line)
                            if api_url and api_url not in seen_api_urls:
                                seen_api_urls.add(api_url)
                                outfile.write(f"##### 檔案：{fname} #####\n")
                                outfile.writelines(current_block)
                                outfile.write("\n")
                            current_block = []
                        else:
                            current_block.append(line)

    print(f"✅ 已整合完成（排除重複 API），輸出到：{merged_path}")

# 使用方法
if __name__ == "__main__":
    merge_all_txt_in_output()