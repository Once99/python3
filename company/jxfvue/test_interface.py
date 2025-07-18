import requests
import json
import time

CODE_HINTS = {
    "101": "⚠️ 系統繁忙，請稍後再試",
    "116": "⚠️ 參數錯誤",
    "30000": "⚠️ 尚未登入",
    "60000": "⚠️ 用戶資訊失效或缺失",
    "20000": "✅ 成功"
}


def check_single_api(full_url: str, method='POST', data=None, headers=None):
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
    while True:
        full_url = input("🔗 請輸入完整 API URL（或輸入 q 結束）：\n").strip()
        if full_url.lower() == 'q':
            break
        param_str = input("📤 請輸入 JSON 格式的參數（預設為空）：\n").strip()
        try:
            params = json.loads(param_str) if param_str else {}
        except json.JSONDecodeError:
            print("⚠️ 參數不是合法的 JSON 格式，請重新輸入。")
            continue
        method = input("📨 請輸入請求方法（GET 或 POST，預設為 POST）：\n").strip().upper() or "POST"
        check_single_api(full_url, method=method, data=params)


if __name__ == "__main__":
    main()