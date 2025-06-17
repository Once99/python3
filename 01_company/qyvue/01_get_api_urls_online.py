import requests
import json
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from urllib.parse import urlparse
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
        base = f"{dir_parts[-2]}_{os.path.splitext(dir_parts[-1])[0]}"
    else:
        base = os.path.splitext(dir_parts[-1])[0]

    # 只接受 ?action 參數，忽略其他參數
    if "action=" in parsed.query:
        query_parts = [q for q in parsed.query.split("&") if q.startswith("action=")]
        query = "_".join(q.replace("=", "_") for q in query_parts)
        page_name = f"{base}_{query}"
    else:
        page_name = base

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
    output_file = os.path.join(output_dir, f"{page_name}_api_info.txt")

    # 清空請求記錄
    del driver.requests
    print(f"\n➡️ 訪問：{start_url}")
    driver.get(start_url)

    try:
        time.sleep(5)
    except Exception as e:
        print(f"⚠️ 固定等待失敗：{e}")

    # 收集 PHP API 請求資訊
    api_infos = []
    for req in driver.requests:
        if req.response and is_php_api(req.url):
            try:
                full_url = req.url
                method = req.method
                headers = dict(req.headers)
                data = req.body.decode(errors="ignore") if req.body else ""

                print(f"\n🔍 測試接口: {full_url}")
                print(f"📤 發送參數: {data}")
                start_time = time.time()

                if method.upper() == 'GET':
                    r = requests.get(full_url, headers=headers, params=data)
                else:
                    r = requests.post(full_url, headers=headers, data=data)

                elapsed = time.time() - start_time
                print(f"✅ 狀態碼: {r.status_code} | ⏱️ 響應時間: {elapsed:.2f} 秒")

                try:
                    json_data = r.json()
                    code = str(json_data.get("code", ""))
                    message = json_data.get("msg") or json_data.get("message", "")
                    preview = json.dumps(json_data, indent=2, ensure_ascii=False)[:500]
                except Exception:
                    code = ""
                    message = ""
                    preview = r.text[:500]

                api_infos.append((full_url, r.status_code, data, preview))
            except Exception as e:
                print(f"❌ 測試失敗：{e}")

    # 寫入個別頁面檔案，每筆資料條列式說明
    with open(output_file, "w", encoding="utf-8") as f:
        for url, status_code, request_body, response_body in sorted(api_infos, key=lambda x: x[0]):
            f.write(f"1.訪問頁面：{start_url}\n")
            f.write(f"2.API地址：{url}\n")
            f.write(f"3.接口狀態：{status_code}\n")
            f.write(f"4.接口參數：{request_body}\n")
            f.write(f"5.接口返回：{response_body}\n")
            f.write("--------------------------------------------------\n\n")

    print(f"📄 寫入 {output_file}（{len(api_infos)} 筆）")
    for url, _, _, _ in sorted(api_infos, key=lambda x: x[0]):
        print("✅", url)

    all_php_urls.update([info[0] for info in api_infos])

    # 搜尋內部連結並遞迴訪問
    internal_links = get_all_internal_links(driver, start_url)
    slot_game_visited = False
    for link in internal_links:
        link_cleaned = link.split("#")[0]

        # 特別處理 slotGame.jsp，只訪問其中一個
        if "slotGame.jsp" in link_cleaned:
            if slot_game_visited:
                continue
            else:
                slot_game_visited = True

        if link_cleaned not in visited:
            visit_and_collect(driver, link, wait_selector=None, visited=visited, all_php_urls=all_php_urls)

def main():
    # 清空 output 目錄下所有 .txt 檔案
    output_dir = "output"
    if os.path.exists(output_dir):
        for file in os.listdir(output_dir):
            if file.endswith(".txt"):
                os.remove(os.path.join(output_dir, file))
    else:
        os.makedirs(output_dir, exist_ok=True)

    options = Options()
    driver = webdriver.Chrome(options=options)  # 可視化登入

    login_url = "https://qy212.vip/login.jsp"
    print(f"🔓 請登入：{login_url}")
    driver.get(login_url)
    input("✅ 登入成功後請按 Enter 繼續...")

    # 起始頁面列表（不含 wait_for）
    start_pages = [
        "https://qy212.vip/index.jsp"
    ]

    all_php_urls = set()
    visited_links = set()

    url = start_pages[0]
    visit_and_collect(driver, start_url=url, wait_selector=None, visited=visited_links, all_php_urls=all_php_urls)

    driver.quit()

if __name__ == "__main__":
    main()