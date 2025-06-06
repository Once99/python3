from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import requests
import os
import time

# === 請修改這裡 ===
VIDEO_PAGE_URL = "https://pvvstream.pro/video/11304934"  # 影片頁面網址
DOWNLOAD_DIR = os.path.expanduser("~/Downloads")         # 儲存資料夾
# ==================

def setup_browser():
    options = Options()
    # options.add_argument("--headless")  # 除錯時建議註解
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280,800")
    return webdriver.Chrome(options=options)

def get_video_url_and_cookies(driver):
    driver.get(VIDEO_PAGE_URL)
    time.sleep(3)  # 等待 JS 載入，亦可用 WebDriverWait

    try:
        video_tag = driver.find_element(By.TAG_NAME, "video")
        video_url = video_tag.get_attribute("src")
        cookies = driver.get_cookies()
        print(f"🎯 抓到影片連結：{video_url}")
        return video_url, cookies
    except Exception as e:
        print(f"❌ 抓不到影片連結：{e}")
        return None, None

def download_video_with_cookies(video_url, cookies):
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": VIDEO_PAGE_URL
    }

    session = requests.Session()
    for cookie in cookies:
        session.cookies.set(cookie['name'], cookie['value'])

    filename = os.path.basename(video_url.split('?')[0])
    file_path = os.path.join(DOWNLOAD_DIR, filename)

    print(f"📥 開始下載：{file_path}")
    try:
        with session.get(video_url, headers=headers, stream=True) as r:
            r.raise_for_status()
            with open(file_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        print(f"✅ 下載完成：{file_path}")
    except Exception as e:
        print(f"❌ 下載失敗：{e}")

def main():
    driver = setup_browser()
    try:
        video_url, cookies = get_video_url_and_cookies(driver)
        if video_url:
            download_video_with_cookies(video_url, cookies)
        else:
            print("⚠️ 未擷取到影片 URL")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()