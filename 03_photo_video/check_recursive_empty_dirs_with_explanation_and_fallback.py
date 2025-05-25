import os
import unicodedata

EXCLUDED_FILES = {".DS_Store", ".gitkeep", "Thumbs.db"}

def explain_items_in_directory(path):
    """列出所有檔案並說明每一項是否被排除"""
    print("   📦 目錄內容診斷：")
    try:
        items = sorted(os.listdir(path))
        if not items:
            print("     （空目錄）")
            return []

        valid_files = []

        for f in items:
            full = os.path.join(path, f)
            label = []

            if f in EXCLUDED_FILES:
                label.append("🚫 排除檔")
            if os.path.isdir(full):
                label.append("📂 資料夾")
            if os.path.islink(full):
                label.append("🔗 符號連結")
            if os.path.isfile(full):
                label.append("✅ 實體檔案")
                if f not in EXCLUDED_FILES:
                    valid_files.append(f)

            if not label:
                label.append("❓ 無法判斷")

            print(f"     - {repr(f)} → {'，'.join(label)}")

        return valid_files

    except Exception as e:
        print(f"     ⚠️ 無法讀取內容：{e}")
        return []

def method_1_listdir_isfile(path):
    try:
        return not any(
            os.path.isfile(os.path.join(path, f)) and f not in EXCLUDED_FILES
            for f in os.listdir(path)
        )
    except Exception:
        return False

def method_2_scandir(path):
    try:
        with os.scandir(path) as it:
            return not any(entry.name not in EXCLUDED_FILES for entry in it)
    except Exception:
        return False

def method_3_listdir_isdir(path):
    try:
        return not any(
            os.path.isdir(os.path.join(path, f)) and f not in EXCLUDED_FILES
            for f in os.listdir(path)
        )
    except Exception:
        return False

def method_4_listdir_isfile_all(path):
    try:
        items = [f for f in os.listdir(path) if f not in EXCLUDED_FILES]
        if not items:
            return True
        return all(not os.path.isfile(os.path.join(path, f)) for f in items)
    except Exception:
        return False

def is_combined_empty(path):
    checks = [
        method_1_listdir_isfile(path),
        method_2_scandir(path),
        method_3_listdir_isdir(path),
        method_4_listdir_isfile_all(path),
    ]
    return all(checks)

def suggest_similar_from_parent(path):
    parent = os.path.dirname(path)
    print(f"\n🔍 無法找到該目錄，列出上層目錄：{parent}")
    if not os.path.exists(parent):
        print("   ⚠️ 父層目錄也不存在")
        return

    try:
        entries = os.listdir(parent)
        print("   📂 子項目：")
        for e in sorted(entries):
            full = os.path.join(parent, e)
            note = []
            if os.path.isdir(full): note.append("📁")
            if os.path.islink(full): note.append("🔗")
            print(f"     - {repr(e)} {' '.join(note)}")
    except Exception as e:
        print(f"   ⚠️ 無法列出子項目：{e}")

def check_directory(path):
    print(f"\n📁 檢查目錄：{path}")
    if not os.path.exists(path):
        print("   ⚠️ 該目錄不存在")
        suggest_similar_from_parent(path)
        return

    valid_files = explain_items_in_directory(path)

    if valid_files:
        print("   📄 有效檔案：")
        for f in valid_files:
            print(f"     ✅ {f}")
    else:
        print("   📄 無有效檔案（空或僅含特殊/資料夾）")

    is_empty = is_combined_empty(path)
    print(f"   綜合判斷：{'✅ 空目錄' if is_empty else '❌ 非空目錄'}")

def scan_directory_recursively(base_dir):
    print(f"\n🔽 掃描主目錄：{base_dir}")
    if not os.path.exists(base_dir):
        print("⚠️  目錄不存在")
        suggest_similar_from_parent(base_dir)
        return

    for root, _, _ in os.walk(base_dir):
        check_directory(root)

def main():
    dirs_to_check = [
        "/Volumes/My Passport/01_逼波葛格/01_開始賺錢/02_我的創業/03_Oppa Internet Cafe/我的檔案/我的設計/佈局規劃/v1/v2/",
        "/Volumes/My Passport/02_我的照片/【　Ａ、全家の照片　】/01_12_Pampamga_CongDadongDam/Cong Dadong Dam/Hungry Neighbors Clark",
        "/Volumes/My Passport/02_我的照片/【　Ａ、全家の照片　】/【　2024年　】/【    下半年の思考人生    】/Casino/10_13_COD_NOBU",
        "/Volumes/My Passport/02_我的照片/【　Ａ、全家の照片　】/【　Fishing　】/【　Freshwater Fishing Village　】/04_09_SuperHot",
        "/Volumes/My Passport/02_我的照片/【　Ａ、在菲照片　】/2015_菲律賓流浪記/2015-11-28-與外國人的接觸/新增資料夾/Originals",
        "/Volumes/My Passport/02_我的照片/【　Ａ、在菲照片　】/2015_菲律賓流浪記/夜生活/Girls/",
        "/Volumes/My Passport/07_整理檔案/2025_花花世界/01_癡情/ED_MOSAIC/",
        "/Volumes/My Passport/07_整理檔案/2025_花花世界/01_癡情/iBras_store/",
        "/Volumes/My Passport/07_整理檔案/2025_花花世界/03_小菲/小菲影片整理/PINAY_KIDS/Filter/",
        "/Volumes/My Passport/07_整理檔案/2025_花花世界/03_小菲/小菲影片整理/PINAY_KIDS/Good/",
        "/Volumes/My Passport/07_整理檔案/2025_花花世界/03_小菲/小菲影片整理/PINAY_SCANDALS/"
    ]

    print("🚀 遞迴掃描所有子目錄（含每項解釋 + 錯字建議）\n")

    for base_dir in dirs_to_check:
        # Unicode normalization 處理
        base_dir = unicodedata.normalize('NFC', base_dir)
        scan_directory_recursively(base_dir)

if __name__ == '__main__':
    main()
