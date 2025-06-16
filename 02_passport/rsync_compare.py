import os
import subprocess
from datetime import datetime

def main():
    source_dir = "/Volumes/My Passport/"
    if not source_dir or not os.path.isdir(source_dir):
        print("❌ 來源目錄無效或不存在")
        return

    # Debug: 列出來源資料夾內容（僅前幾個檔案）
    print("來源資料夾內容（僅列出前幾個檔案）：")
    file_count = 0
    for root, dirs, files in os.walk(source_dir):
        for name in files:
            print(os.path.join(root, name))
            file_count += 1
            if file_count >= 20:
                print("...（檔案太多，僅顯示前 20 筆）")
                break
        if file_count >= 20:
            break
    if file_count == 0:
        print("⚠️ 找不到任何檔案。")


    target_dir = "/Volumes/TOSHIBA EXT/2025-06-06/"
    if not target_dir or not os.path.isdir(target_dir):
        print("❌ 目的目錄無效或不存在")
        return

    # Debug: 列出來源資料夾內容（僅前幾個檔案）
    print("目錄資料夾內容（僅列出前幾個檔案）：")
    file_count = 0
    for root, dirs, files in os.walk(target_dir):
        for name in files:
            print(os.path.join(root, name))
            file_count += 1
            if file_count >= 20:
                print("...（檔案太多，僅顯示前 20 筆）")
                break
        if file_count >= 20:
            break
    if file_count == 0:
        print("⚠️ 找不到任何檔案。")

    cmd = [
        "rsync",
        "-avhn",  # dry-run 模式，只列出差異
        "--delete",
        "--exclude='.DS_Store'",
        "--exclude='__MACOSX'",
        "--exclude='._*'",
        "--iconv=UTF-8-MAC,UTF-8",
        source_dir + "/",
        target_dir + "/"
    ]

    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output = result.stdout.decode('utf-8', errors='replace')  # 無法解碼的字元將被替換為 �

    print("rsync 原始輸出：")
    print(output)

    # 過濾掉 ._ 開頭的行
    filtered_output = "\n".join(
        line for line in output.splitlines()
        if not os.path.basename(line.strip()).startswith("._")
    )

    # 儲存日誌
    log_dir = os.path.expanduser("~/Downloads")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = os.path.join(log_dir, f"rsync_diff_log_{timestamp}.txt")

    with open(log_path, "w", encoding="utf-8") as f:
        f.write(filtered_output)

    # 預覽前 20 行
    preview = "\n".join(filtered_output.splitlines()[:20])
    if len(filtered_output.splitlines()) > 20:
        preview += "\n...\n(輸出已截斷)"

    print(f"比對完成，日誌已儲存：{log_path}\n")
    print("部分預覽：\n")
    print(preview)

if __name__ == "__main__":
    main()