import os
import requests
from bs4 import BeautifulSoup

# 是否要自動下載
AUTO_DOWNLOAD = True

# HTML 檔案路徑（修正：與 .py 同層）
html_path = os.path.join(os.path.dirname(__file__), "PS.html")

# 根據檔名建立對應的資料夾
html_name = os.path.splitext(os.path.basename(html_path))[0]  # 取出 JILI
SAVE_DIR = os.path.expanduser(f"~/Downloads/output/{html_name}")
os.makedirs(SAVE_DIR, exist_ok=True)

# 讀取 HTML
with open(html_path, "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')
image_tasks = []

# 擷取每個遊戲項目
for game in soup.select('.game_item'):
    name_tag = game.select_one('.game_top > span')
    if not name_tag:
        continue

    raw = name_tag.text
    parts = raw.split(',')
    name_field = next((p for p in parts if 'name:' in p), None)
    if not name_field:
        continue
    game_name = name_field.replace('name:', '').strip()

    img_tag = game.find('img')
    if img_tag and img_tag.get('src'):
        img_url = img_tag['src'].split('?')[0]
        image_tasks.append((game_name, img_url))

# 顯示擷取結果
print(f"\n📋 擷取到以下圖片（共 {len(image_tasks)} 張）：")
for name, url in image_tasks:
    print(f"📌 {name} → {url}")

# 判斷是否下載
if not AUTO_DOWNLOAD:
    print("\n❌ 已設定為不自動下載")
else:
    for name, url in image_tasks:
        ext = os.path.splitext(url)[1]
        if not ext or len(ext) > 6:
            ext = ".webp"
        safe_name = name.replace('/', '_')
        file_path = os.path.join(SAVE_DIR, f"{safe_name}{ext}")
        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            with open(file_path, 'wb') as f:
                f.write(r.content)
            print(f"✅ 已下載：{file_path}")
        except Exception as e:
            print(f"❌ {name} 圖片下載失敗：{e}")
