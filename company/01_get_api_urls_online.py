from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urlparse, urljoin
import os
import time

def is_php_api(url):
    return url.endswith('.php') or '.php?' in url

def extract_domain_and_page_name(full_url):
    parsed = urlparse(full_url)
    domain = parsed.hostname or "unknown"
    domain_name = domain.split('.')[0]
    dir_parts = parsed.path.strip("/").split("/")
    if len(dir_parts) > 1:
        page_name = f"{dir_parts[-2]}_{os.path.splitext(dir_parts[-1])[0]}"
    else:
        page_name = os.path.splitext(dir_parts[-1])[0]
    return domain_name, page_name

def is_internal_link(base_url, link_url):
    base_domain = urlparse(base_url).netloc
    test_domain = urlparse(link_url).netloc
    return base_domain == test_domain

def get_all_internal_links(driver, base_url):
    anchors = driver.find_elements(By.TAG_NAME, "a")
    links = set()
    for a in anchors:
        href = a.get_attribute("href")
        if href and href.startswith("http") and is_internal_link(base_url, href):
            href = href.split("#")[0]  # 移除 fragment
            links.add(href)
    return links

def visit_and_collect(driver, start_url, wait_selector=None, visited=None, all_php_urls=None):
    if visited is None:
        visited = set()
    if all_php_urls is None:
        all_php_urls = set()

    url_cleaned = start_url.split("#")[0]
    if url_cleaned in visited:
        return
    visited.add(url_cleaned)

    # 在訪問前檢查檔案是否已存在，若存在則直接跳過
    domain_name, page_name = extract_domain_and_page_name(start_url)
    output_dir = "output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"{page_name}_php_api.txt")
    if os.path.exists(output_file):
        print(f"⏩ 已存在 {output_file}，跳過")
        return

    # 清空請求記錄
    del driver.requests
    print(f"\n➡️ 訪問：{start_url}")
    driver.get(start_url)

    try:
        time.sleep(5)
    except Exception as e:
        print(f"⚠️ 固定等待失敗：{e}")

    # 收集 .php API 請求
    php_api_urls = set()
    for req in driver.requests:
        if req.response and is_php_api(req.url):
            php_api_urls.add(req.url)

    # 寫入個別頁面檔案
    with open(output_file, "w", encoding="utf-8") as f:
        for url in sorted(php_api_urls):
            f.write(url + "\n")

    # 追加來源頁面資訊
    with open(output_file, "a", encoding="utf-8") as f:
        f.write(f"\n# Source Page: {start_url}\n")

    print(f"📄 寫入 {output_file}（{len(php_api_urls)} 筆）")
    for url in sorted(php_api_urls):
        print("✅", url)

    all_php_urls.update(php_api_urls)

    # 搜尋內部連結並遞迴訪問
    internal_links = get_all_internal_links(driver, start_url)
    for link in internal_links:
        link_cleaned = link.split("#")[0]
        if link_cleaned not in visited:
            visit_and_collect(driver, link, wait_selector=None, visited=visited, all_php_urls=all_php_urls)

def main():
    options = Options()
    driver = webdriver.Chrome(options=options)  # 可視化登入

    login_url = "https://qy212.vip/login.jsp"
    print(f"🔓 請登入：{login_url}")
    driver.get(login_url)
    input("✅ 登入成功後請按 Enter 繼續...")

    # 起始頁面列表（不含 wait_for）
    start_pages = [
        "https://qy212.vip/index.jsp",
        "https://qy212.vip/userManage.php?action=1",
        "https://qy212.vip/mobile/index.jsp",
        "https://qy212.vip/mobile/userCenterNew.jsp"
    ]

    all_php_urls = set()
    visited_links = set()

    for url in start_pages:
        visit_and_collect(
            driver,
            start_url=url,
            wait_selector=None,
            visited=visited_links,
            all_php_urls=all_php_urls
        )

    # 寫入總檔案
    all_file_path = os.path.join("output", "all_php_api.txt")
    with open(all_file_path, "w", encoding="utf-8") as f:
        for url in sorted(all_php_urls):
            f.write(url + "\n")

    print(f"\n📊 總共收集 {len(all_php_urls)} 筆 .php API，寫入：{all_file_path}")
    driver.quit()

if __name__ == "__main__":
    main()