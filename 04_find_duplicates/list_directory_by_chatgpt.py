import os
import re
from datetime import datetime

# === 設定來源資料夾 ===
SOURCE_ROOT = "/Users/oncechen/Library/CloudStorage/GoogleDrive-howard123702002@gmail.com/我的雲端硬碟"
now = datetime.now()
folder_name = f"Output_{now.hour:02d}_{now.minute:02d}"
TARGET_ROOT = os.path.expanduser(f"~/Downloads/{folder_name}")

def should_rename(name):
    # 是否包含英文字母（A-Z or a-z）
    return bool(re.search(r"[A-Za-z]", name))

def sanitize_folder_name(name):
    # 移除特殊符號與日文、全形空白
    name = name.replace("　", " ").replace("の", "_")
    name = re.sub(r"[【】「」『』\[\]（）()]", "", name)
    name = re.sub(r"\s+", "_", name)

    # 僅保留前綴的數字與中文
    match = re.match(r"^(\d{2,})_([\u4e00-\u9fa5]+)", name)
    if match:
        return f"{match.group(1)}_{match.group(2)}"
    else:
        # 若無數字前綴，則盡量保留中文
        zh_only = re.sub(r"[^\u4e00-\u9fa5]", "", name)
        return zh_only if zh_only else name

def create_structure_with_selective_rename(src_path, dst_path):
    try:
        for item in sorted(os.listdir(src_path)):
            src_full = os.path.join(src_path, item)
            if os.path.isdir(src_full):
                new_name = sanitize_folder_name(item) if should_rename(item) else item
                dst_full = os.path.join(dst_path, new_name)
                os.makedirs(dst_full, exist_ok=True)
                create_structure_with_selective_rename(src_full, dst_full)
    except PermissionError:
        print(f"⚠️ 無權限讀取：{src_path}")

if __name__ == "__main__":
    print(f"📂 正在建立目錄結構到：{TARGET_ROOT}")
    os.makedirs(TARGET_ROOT, exist_ok=True)
    create_structure_with_selective_rename(SOURCE_ROOT, TARGET_ROOT)
    print("✅ 完成！已根據條件建立優化後目錄。")
