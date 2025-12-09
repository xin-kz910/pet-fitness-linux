# sender.py
"""
負責：
1. 向 /api/user/server_status 查詢 user 目前在 A/B/C 哪一台。
2. 用正確的 prefix 呼叫 /api/pet/status 拿 pet_id。
3. 組出正確的 update_url（/serverX/api/pet/update）。
4. 把「運動次數」送到 update_url。

這支可以被 detector_opencv.py 匯入，也可以單獨執行測試。
"""

from typing import Optional, Dict

import requests

from config import (
    BASE_URL,
    USER_ID,
    SERVER_STATUS_URL,
    PET_STATUS_PATH,
    UPDATE_PATH,
    SERVER_PREFIX_MAP,
)

_detector_config_cache: Optional[Dict] = None


def load_detector_config(force_refresh: bool = False) -> Optional[Dict]:
    """
    組出給偵測器用的設定：
    {
        "user_id": 1,
        "pet_id": 1,
        "server_id": "B",
        "update_url": "http://.../serverB/api/pet/update"
    }
    """
    global _detector_config_cache

    if _detector_config_cache is not None and not force_refresh:
        return _detector_config_cache

    # Step 1: 向 /api/user/server_status 查詢目前 server_id
    print(f"[CONFIG] 查詢使用者目前 server：{SERVER_STATUS_URL}?user_id={USER_ID}")
    try:
        resp = requests.get(SERVER_STATUS_URL, params={"user_id": USER_ID}, timeout=3)
    except requests.exceptions.RequestException as exc:
        print(f"[CONFIG][ERROR] 無法連線到 server_status API：{exc}")
        return None

    try:
        resp_json = resp.json()
    except Exception:
        print(f"[CONFIG][ERROR] server_status 回應不是合法 JSON，status={resp.status_code}")
        return None

    if not resp_json.get("success", False):
        print("[CONFIG][ERROR] server_status 回傳錯誤：", resp_json.get("error"))
        return None

    data = resp_json.get("data") or {}
    server_id = data.get("server_id")
    if not server_id:
        print("[CONFIG][ERROR] server_status 缺少 server_id")
        return None

    # Step 2: 把 server_id 映射成 /serverA /serverB /serverC prefix
    prefix = SERVER_PREFIX_MAP.get(server_id)
    if not prefix:
        print(f"[CONFIG][ERROR] 未知的 server_id：{server_id}")
        return None

    # Step 3: 呼叫該伺服器的 /api/pet/status 拿 pet_id
    pet_status_url = f"{BASE_URL}{prefix}{PET_STATUS_PATH}"
    print(f"[CONFIG] 查詢寵物狀態：{pet_status_url}?user_id={USER_ID}")

    try:
        resp2 = requests.get(pet_status_url, params={"user_id": USER_ID}, timeout=3)
    except requests.exceptions.RequestException as exc:
        print(f"[CONFIG][ERROR] 無法連線到 pet_status API：{exc}")
        return None

    try:
        resp2_json = resp2.json()
    except Exception:
        print(f"[CONFIG][ERROR] pet_status 回應不是合法 JSON，status={resp2.status_code}")
        return None

    if not resp2_json.get("success", False):
        print("[CONFIG][ERROR] pet_status 回傳錯誤：", resp2_json.get("error"))
        return None

    pet_data = resp2_json.get("data") or {}
    pet_id = pet_data.get("pet_id")
    if not pet_id:
        print("[CONFIG][ERROR] pet_status 缺少 pet_id")
        return None

    # Step 4: 組出 update_url
    update_url = f"{BASE_URL}{prefix}{UPDATE_PATH}"

    cfg = {
        "user_id": USER_ID,
        "pet_id": pet_id,
        "server_id": server_id,
        "update_url": update_url,
    }

    _detector_config_cache = cfg
    print(f"[CONFIG] 最終偵測器設定：{cfg}")
    return cfg


def send_exercise(exercise_count: int = 1, source: str = "webcam") -> bool:
    """
    傳送一次運動量到後端，依照目前 server_id 自動送到正確伺服器。
    """
    cfg = load_detector_config()
    if not cfg:
        print("[SENDER][ERROR] 無法取得偵測器設定，停止送資料。")
        return False

    update_url = cfg["update_url"]
    payload = {
        "user_id": cfg["user_id"],
        "pet_id": cfg["pet_id"],
        "server_id": cfg["server_id"],
        "exercise_count": exercise_count,
        "source": source,
    }

    print(f"[SENDER] POST {update_url} payload={payload}")

    try:
        resp = requests.post(update_url, json=payload, timeout=3)
    except requests.exceptions.RequestException as exc:
        print(f"[SENDER][ERROR] 無法連線到伺服器：{exc}")
        return False

    try:
        resp_json = resp.json()
    except Exception:
        print(f"[SENDER][ERROR] 回應不是合法 JSON，status={resp.status_code}")
        return False

    success = bool(resp_json.get("success", False))
    print(f"[SENDER] status_code={resp.status_code}, success={success}")

    if not success:
        print("[SENDER] error =", resp_json.get("error"))

    return success


if __name__ == "__main__":
    print("🔍 測試偵測器設定 + 送一次資料 ...")
    cfg = load_detector_config(force_refresh=True)
    if not cfg:
        print("❌ 無法取得偵測器設定，請檢查 /api/user/server_status / /api/pet/status。")
    else:
        print("✅ 已取得設定，開始送一次運動資料 ...")
        ok = send_exercise(exercise_count=1, source="webcam_test")
        print("結果：", "✅ 成功" if ok else "❌ 失敗")
