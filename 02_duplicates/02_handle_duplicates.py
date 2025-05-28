import os
from send2trash import send2trash

LOG_FILENAME = "duplicates_log.txt"

def load_duplicates(log_path):
    with open(log_path, 'r', encoding='utf-8') as f:
        content = f.read().strip()
    groups = content.split('---\n')
    return [group.strip().split('\n') for group in groups if group.strip()]

def prompt_delete(group):
    print("\n🧩 找到重複照片：")
    for idx, path in enumerate(group, 1):
        print(f"  {idx}. {path}")
    while True:
        choice = input("請輸入要刪除的編號（0 表示跳過）：")
        if choice.isdigit():
            choice = int(choice)
            if choice == 0:
                print("⏭️  跳過此組")
                return
            elif 1 <= choice <= len(group):
                file_to_delete = group[choice - 1]
                try:
                    send2trash(file_to_delete)
                    print(f"🗑️ 已移至垃圾桶：{file_to_delete}")
                except Exception as e:
                    print(f"❌ 刪除失敗：{e}")
                return
        print("❌ 無效輸入，請重新輸入。")

def main():
    if not os.path.exists(LOG_FILENAME):
        print(f"❌ 找不到 {LOG_FILENAME}，請先執行找重複的腳本")
        return

    duplicate_groups = load_duplicates(LOG_FILENAME)
    for group in duplicate_groups:
        prompt_delete(group)

if __name__ == "__main__":
    main()
