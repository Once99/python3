import os
import hashlib
from tqdm import tqdm
from datetime import datetime
from tkinter import Tk, filedialog, messagebox

# 支援副檔名
IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
VIDEO_EXTS = {'.mp4', '.mov', '.avi', '.mkv', '.flv', '.wmv', '.mpeg', '.webm'}
ALL_EXTS = IMAGE_EXTS.union(VIDEO_EXTS)

def get_file_hash(file_path, chunk_size=4096):
    """計算檔案 SHA256 雜湊"""
    hasher = hashlib.sha256()
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(chunk_size), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as e:
        print(f"❌ 無法讀取 {file_path}：{e}")
        return None

def find_duplicates(folder):
    """先以檔案大小分組，再計算 hash 以提高效能"""
    size_map = {}
    hashes = {}
    duplicates = []

    print("📦 掃描檔案中...")

    for root, _, files in os.walk(folder):
        for filename in files:
            ext = os.path.splitext(filename)[1].lower()
            if ext in ALL_EXTS:
                full_path = os.path.join(root, filename)
                try:
                    size = os.path.getsize(full_path)
                    size_map.setdefault(size, []).append(full_path)
                except Exception as e:
                    print(f"❌ 無法取得檔案大小：{full_path} - {e}")

    candidate_files = []
    for size, paths in size_map.items():
        if len(paths) > 1:  # 僅對同大小檔案進行 hash
            candidate_files.extend(paths)

    print(f"🔍 預計檢查 {len(candidate_files)} 筆可能重複檔案")
    for path in tqdm(candidate_files, desc="🔑 計算檔案雜湊"):
        file_hash = get_file_hash(path)
        if file_hash:
            if file_hash in hashes:
                duplicates.append((hashes[file_hash], path))
            else:
                hashes[file_hash] = path

    return duplicates


def write_duplicates(duplicates, timestamp):
    output_file = f"{timestamp}_duplicates_files.txt"
    grouped = {}
    for original, dup in duplicates:
        grouped.setdefault(original, []).append(dup)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("📁 重複檔案清單：\n\n")
        for original, dup_list in grouped.items():
            f.write(f"🟡 原始檔案: {original}\n")
            for dup in dup_list:
                try:
                    size = os.path.getsize(dup)
                    f.write(f"    🔁 重複檔案: {dup}\n")
                    f.write(f"       檔案大小: {size / (1024 * 1024):.2f} MB\n")
                except:
                    f.write(f"    🔁 重複檔案: {dup}（無法取得大小）\n")
            f.write("------------------------------------------------------------\n")
    print(f"✅ 重複檔案已寫入：{output_file}")

def remove_duplicates(duplicates, timestamp):
    removed_log = f"{timestamp}_duplicates_remove.txt"
    with open(removed_log, 'w', encoding='utf-8') as f:
        f.write("🗑️ 已刪除的重複檔案清單：\n\n")
        for _, dup in duplicates:
            try:
                os.remove(dup)
                f.write(f"{dup}\n")
            except Exception as e:
                f.write(f"{dup} ❌ 刪除失敗：{e}\n")
    print(f"🗑️ 刪除紀錄已寫入：{removed_log}")

if __name__ == "__main__":
    Tk().withdraw()
    folder = filedialog.askdirectory(title="請選擇要掃描的資料夾")

    if not folder or not os.path.isdir(folder):
        print("❌ 未選取有效資料夾")
    else:
        timestamp = datetime.now().strftime('%m%d_%H%M')
        duplicates = find_duplicates(folder)
        if duplicates:
            write_duplicates(duplicates, timestamp)

            # 詢問是否刪除
            confirm = messagebox.askyesno("刪除確認", f"找到 {len(duplicates)} 個重複檔案，是否要刪除？")
            if confirm:
                remove_duplicates(duplicates, timestamp)
                messagebox.showinfo("完成", "重複檔案已刪除")
            else:
                messagebox.showinfo("保留檔案", "已保留所有檔案")
        else:
            messagebox.showinfo("沒有重複檔案", "沒有找到重複的檔案")
