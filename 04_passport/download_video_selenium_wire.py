from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options
import requests
import os
import time

# 修改為你的影片播放頁面網址
VIDEO_PAGE_URL = "https://ukdevilz.com/watch/11304934_155266872"
DOWNLOAD_DIR = os.path.expanduser("~/Downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def setup_browser():
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # 除錯可先註解
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1280,800")

    seleniumwire_options = {
        'disable_encoding': True  # 避免自動解壓縮 gzip
    }

    return webdriver.Chrome(options=chrome_options, seleniumwire_options=seleniumwire_options)

def find_mp4_request(driver):
    driver.get(VIDEO_PAGE_URL)
    time.sleep(5)  # 等待 JS 載入影片請求

    print("🔍 正在尋找影片請求 (.mp4)...")
    for request in driver.requests:
        if request.response and ".mp4" in request.url:
            print(f"🎯 找到影片連結：{request.url}")
            return request
    return None

def download_video(request):
    headers = {k: v for k, v in request.headers.items() if k.lower() != 'host'}
    url = request.url
    filename = os.path.basename(url.split('?')[0])
    file_path = os.path.join(DOWNLOAD_DIR, filename)

    print(f"📥 開始下載：{file_path}")
    try:
        with requests.get(url, headers=headers, stream=True) as r:
            r.raise_for_status()
            with open(file_path, "wb") as f:
                for chunk in r.iter_content(8192):
                    f.write(chunk)
        print("✅ 下載完成")
    except Exception as e:
        print(f"❌ 下載失敗：{e}")

def main():
    driver = setup_browser()
    try:
        request = find_mp4_request(driver)
        if request:
            download_video(request)
        else:
            print("❌ 沒有找到影片連結")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()