import os

def merge_all_txt_in_output(output_dir="output", merged_filename="merged_api_all.txt"):
    merged_path = os.path.join(output_dir, merged_filename)

    with open(merged_path, 'w', encoding='utf-8') as outfile:
        for fname in sorted(os.listdir(output_dir)):
            if fname.endswith('.txt') and fname != merged_filename:
                file_path = os.path.join(output_dir, fname)
                with open(file_path, 'r', encoding='utf-8') as infile:
                    outfile.write(f"##### 檔案：{fname} #####\n")
                    outfile.writelines(infile.readlines())
                    outfile.write("\n\n")

    print(f"✅ 已整合完成，輸出到：{merged_path}")

# 使用方法
if __name__ == "__main__":
    merge_all_txt_in_output()