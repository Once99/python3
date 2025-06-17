import os
from send2trash import send2trash
from tkinter import Tk, filedialog

def select_log_file():
    root = Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="選擇 duplicates_log.txt 檔案",
        filetypes=[("Text Files", "*.txt")]
    )
    return file_path

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
    log_path = select_log_file()
    if not log_path or not os.path.exists(log_path):
        print("❌ 未選取有效的 log 檔案，請重新執行。")
        return

    duplicate_groups = load_duplicates(log_path)
    for group in duplicate_groups:
        prompt_delete(group)

if __name__ == "__main__":
    main()
