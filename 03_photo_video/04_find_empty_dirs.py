import os

DIRS_TO_CHECK = [
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

MEDIA_EXTS = {
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp',
    '.mp4', '.mov', '.avi', '.mkv', '.flv', '.wmv', '.mpeg', '.webm'
}

def is_media_file(filename):
    parts = filename.lower().split(".")
    if len(parts) < 2:
        return False
    for i in range(1, len(parts)):
        ext = "." + parts[i]
        if ext in MEDIA_EXTS:
            return True
    return False

def list_media_files(path):
    """遞迴回傳該資料夾中所有圖片/影片檔案（完整路徑）"""
    media_files = []
    for root, dirs, files in os.walk(path):
        for f in files:
            if is_media_file(f):
                media_files.append(os.path.join(root, f))
    return media_files

def main():
    not_found = []

    for d in DIRS_TO_CHECK:
        print("=" * 80)
        if not os.path.exists(d):
            print(f"⚠️  目錄不存在：{d}")
            not_found.append(d)
            continue

        media_files = list_media_files(d)
        if media_files:
            print(f"❌ 非空目錄（含圖片或影片）：{d}")
            print("🔍 找到的媒體檔案：")
            for f in media_files:
                print(f"   - {f}")
        else:
            print(f"✅ 空目錄（無圖片或影片）：{d}")

    print("\n🧾 檢查完成")
    if not_found:
        print(f"⚠️ 找不到的目錄數量：{len(not_found)}")
        for d in not_found:
            print(f"  - {d}")

if __name__ == '__main__':
    main()
