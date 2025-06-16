from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
import requests
import json
from urllib.parse import urljoin

BASE_URL = "https://qyvue.itomtest.com"

# 自動登入並取得 cookies
def login_and_get_cookies():
    options = Options()
    options.add_argument("--headless=new")  # 移除這行即可看到視窗
    driver = webdriver.Chrome(options=options)

    try:
        driver.get(f"{BASE_URL}/login")
        print("請手動登入，登入完成後按 Enter 繼續...")
        input()

        cookies = driver.get_cookies()
        cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
        return cookie_dict
    finally:
        driver.quit()

# 帶著 cookie 測試 API
def check_api_with_cookies(api_path, cookies, method='POST', data=None):
    full_url = urljoin(BASE_URL, api_path)
    print(f"\n🔍 正在測試: {full_url}")

    try:
        if method.upper() == 'GET':
            response = requests.get(full_url, cookies=cookies)
        else:
            response = requests.post(full_url, data=data, cookies=cookies)

        print(f"✅ 狀態碼: {response.status_code}")
        try:
            json_data = response.json()
            print(f"📦 JSON 前100字:\n{json.dumps(json_data, indent=2, ensure_ascii=False)[:100]}...\n")
        except Exception:
            print(f"⚠️ 無法解析 JSON:\n{response.text[:200]}...\n")

    except requests.RequestException as e:
        print(f"❌ 請求錯誤: {str(e)}")

if __name__ == "__main__":
    cookies = login_and_get_cookies()

    apis_to_check = [
        "/api/getRecords",
        "/api/getBetListRecordV2",
        "/api/getSignOrder",
        "/api/getSignrecord",
        "/api/transferInforRedCoupon",
        "/api/applyRedActiveCoupon",
        "/api/mobileCouponPageList",
        "/api/queryPTLosePromoReccords",
        "/api/querySelfPromotionV3",
        "/api/getNewVipMoney",
        "/api/getNewBirthdayMoney",
        "/api/mobileCouponPageList",
        "/api/getAutoXimaSlotObject",
        "/api/getUserXimaLelve",
        "/api/getYouHuiConfig",
        "/api/getUserInfo",
        "/api/getEbC2CProposal",
        "/api/getUserAllWthdrawAmount"
    ]

    for path in apis_to_check:
        check_api_with_cookies(path, cookies)