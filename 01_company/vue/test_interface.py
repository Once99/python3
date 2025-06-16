import requests
import json
from urllib.parse import urljoin
import time

BASE_URL = "https://qyvue.itomtest.com"
DEFAULT_TOKEN = "demo123"

# ✅ 每個 API 對應其參數
API_CONFIGS = [
    {"path": "/api/getRecords", "params": {"transType": "全部", "transStatus": "全部", "timeType": "3"}},
    {"path": "/api/getBetListRecordV2", "params": {"num": "1"}},
    # 其他接口可依需求開啟
]

CODE_HINTS = {
    "101": "⚠️ 系統繁忙，請稍後再試",
    "116": "⚠️ 參數錯誤",
    "30000": "⚠️ 尚未登入",
    "60000": "⚠️ 用戶資訊失效或缺失",
    "20000": "✅ 成功"
}


def check_single_api(api_path: str, method='POST', data=None, headers=None):
    full_url = urljoin(BASE_URL, api_path)

    # 統一加入 token
    if isinstance(data, dict):
        data.setdefault("token", DEFAULT_TOKEN)

    print(f"\n🔍 測試接口: {full_url}")
    print(f"📤 發送參數: {data}")

    try:
        start_time = time.time()
        if method.upper() == 'GET':
            response = requests.get(full_url, headers=headers, params=data)
        else:
            response = requests.post(full_url, data=data, headers=headers)
        elapsed = time.time() - start_time

        print(f"✅ 狀態碼: {response.status_code} | ⏱️ 響應時間: {elapsed:.2f} 秒")

        try:
            json_data = response.json()
            code = str(json_data.get("code", ""))
            message = json_data.get("msg") or json_data.get("message", "")
            hint = CODE_HINTS.get(code, "")
            print(f"📦 回應 code: {code} {hint} | message: {message}")
            preview = json.dumps(json_data, indent=2, ensure_ascii=False)[:200]
            print(f"📄 JSON 預覽:\n{preview}...\n")
        except Exception:
            print("⚠️ 無法解析 JSON：")
            print(response.text[:200] + '...\n')

    except requests.exceptions.RequestException as e:
        print(f"❌ 請求失敗：{e}")


def main():
    input("🔑 請先手動登入（如有登入驗證機制），完成後請按 Enter 繼續...\n")
    for config in API_CONFIGS:
        check_single_api(config["path"], data=config.get("params", {}))


if __name__ == "__main__":
    main()