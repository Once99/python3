from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import requests
import os
import time

VIDEO_PAGE_URL = "https://pvvstream.pro/video/11304934"
DOWNLOAD_DIR = os.path.expanduser("~/Downloads")

def setup_browser():
    options = Options()
    # options.add_argument("--headless")  # 除錯階段可以先註解掉
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280,800")
    return webdriver.Chrome(options=options)

def get_video_url(driver):
    driver.get(VIDEO_PAGE_URL)
    time.sleep(3)  # 可改成 WebDriverWait 更精準

    try:
        video_tag = driver.find_element(By.TAG_NAME, "video")
        video_url = video_tag.get_attribute("src")
        print(f"🎯 抓到影片連結：{video_url}")
        return video_url
    except Exception as e:
        print(f"❌ 找不到 <video>：{e}")
        return None

def download_video(video_url):
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": VIDEO_PAGE_URL
    }

    filename = os.path.basename(video_url.split('?')[0])
    file_path = os.path.join(DOWNLOAD_DIR, filename)

    print(f"📥 開始下載：{file_path}")
    try:
        with requests.get(video_url, headers=headers, stream=True) as r:
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
        video_url = get_video_url(driver)
        if video_url:
            download_video(video_url)
        else:
            print("⚠️ 沒有抓到影片 URL")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()