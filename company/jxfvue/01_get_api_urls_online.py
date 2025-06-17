from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from urllib.parse import urlparse, urljoin
import os
import time
from tqdm import tqdm
import requests  # 確保此行在頂部已引入

def is_api_endpoint(url):
    return '/api/' in url

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

def visit_and_collect(driver, start_url, visited=None, all_api_urls=None):
    """
    訪問指定頁面，收集 API 請求，並遞迴訪問所有內部連結。
    :param driver: Selenium WebDriver
    :param start_url: 起始頁面 URL
    :param visited: 已訪問過的頁面集合
    :param all_api_urls: 已收集的 API URL 集合
    """
    if visited is None:
        visited = set()
    if all_api_urls is None:
        all_api_urls = set()

    url_to_visit = start_url.split("#")[0]
    if url_to_visit in visited:
        return
    visited.add(url_to_visit)

    domain_name, page_name = extract_domain_and_page_name(start_url)
    output_dir = "output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"{page_name}_api.txt")

    # 清空請求記錄
    del driver.requests
    print(f"\n➡️ 訪問：{start_url}")
    driver.get(start_url)

    try:
        time.sleep(5)
    except Exception as e:
        print(f"⚠️ 固定等待失敗：{e}")

    # 收集 .php 或 /api/ 結尾的 API 請求資訊
    api_infos = []
    import requests  # 確保此行在頂部已引入
    for req in driver.requests:
        if req.response and req.method in ("GET", "POST") and ("/api/" in req.url):
            status_code = req.response.status_code
            method = req.method.upper()
            headers = dict(req.headers)
            headers.pop('Content-Length', None)  # 避免錯誤
            headers.pop('Host', None)
            try:
                if method == "GET":
                    resp = requests.get(req.url, headers=headers, timeout=10)
                else:
                    resp = requests.post(req.url, headers=headers, data=req.body or {}, timeout=10)

                status_code = resp.status_code
                try:
                    response_body = resp.text
                    if any(ord(c) < 32 and c not in '\r\n\t' for c in response_body[:50]):
                        raise ValueError("binary content")
                    response_body = response_body[:500]
                except Exception:
                    response_body = "(⚠️ 回傳內容無法解析)"
            except Exception as e:
                response_body = f"(⚠️ 請求失敗: {e})"

            try:
                request_body = req.body.decode("utf-8", errors="ignore") if req.body else ""
            except:
                request_body = ""

            api_infos.append((req.url, status_code, "", request_body, response_body))

    # 寫入個別頁面檔案，每筆資料以條列式格式寫入
    with open(output_file, "w", encoding="utf-8") as f:
        for i, (url, status_code, preview, request_body, response_body) in enumerate(sorted(api_infos, key=lambda x: x[0]), 1):
            f.write(f"1.訪問頁面：{start_url}\n")
            f.write(f"2.API地址：{url}\n")
            f.write(f"3.接口狀態：{status_code}\n")
            f.write(f"4.接口參數：{request_body}\n")
            f.write(f"5.接口返回：{response_body}\n")
            f.write("-" * 50 + "\n\n")

    print(f"📄 寫入 {output_file}（{len(api_infos)} 筆）")
    for url, status_code, preview, request_body, response_body in sorted(api_infos, key=lambda x: x[0]):
        print("✅", url)

    all_api_urls.update([url for url, _, _, _, _ in api_infos])

    # 搜尋內部連結並遞迴訪問
    internal_links = get_all_internal_links(driver, start_url)
    for link in internal_links:
        if link not in visited:
            visit_and_collect(driver, link, visited=visited, all_api_urls=all_api_urls)


def main():
    output_dir = "output"
    if os.path.exists(output_dir):
        for file in os.listdir(output_dir):
            if file.endswith(".txt"):
                os.remove(os.path.join(output_dir, file))

    options = Options()
    driver = webdriver.Chrome(options=options)  # 可視化登入

    login_url = "https://lpapis5811.com/login"
    print(f"🔓 請登入：{login_url}")
    driver.get(login_url)
    input("✅ 登入成功後請按 Enter 繼續...")

    # 起始頁面列表（不含 wait_for）
    start_pages = [
        "https://lpapis5811.com/home",
        "https://lpapis5811.com/slot/PMSLOT"
        "https://lpapis5811.com/bet/nfb",
        "https://lpapis5811.com/HelpCenter",
        "https://lpapis5811.com/events",
        "https://lpapis5811.com/about",
        "https://lpapis5811.com/deposit",
        "https://lpapis5811.com/withdraw",
        "https://lpapis5811.com/transfer",
        "https://lpapis5811.com/record",
        "https://lpapis5811.com/selfPromote",
        "https://lpapis5811.com/belong",
        "https://lpapis5811.com/join",
        "https://lpapis5811.com/events/921",
        "https://lpapis5811.com/Setting"

    ]

    all_api_urls = set()
    visited_links = set()

    for url in tqdm(start_pages):
        visit_and_collect(
            driver,
            start_url=url,
            visited=visited_links,
            all_api_urls=all_api_urls
        )

    driver.quit()

if __name__ == "__main__":
    main()