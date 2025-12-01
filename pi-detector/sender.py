import requests

from config import USER_ID, PET_ID, SERVER_ID, BASE_URL

SERVER_PREFIX_MAP = {
    "A": "/serverA",
    "B": "/serverB",
    "C": "/serverC",
}


def build_server_url(path: str) -> str:
    prefix = SERVER_PREFIX_MAP.get(SERVER_ID, "/serverA")
    return BASE_URL + prefix + path


SERVER_URL = build_server_url("/api/pet/update")


def send_exercise_once():
    """
    單次上報運動事件：
    - 不做動作偵測，只是確認 Pi -> 後端 API 是否通
    - 可給後端 / cron 組測試使用
    """
    payload = {
        "user_id": USER_ID,
        "pet_id": PET_ID,
        "server_id": SERVER_ID,
        "exercise_count": 1,
        "source": "raspberry_pi",
    }

    try:
        r = requests.post(SERVER_URL, json=payload, timeout=3)
        print("[SENDER] Status:", r.status_code)
        try:
            print("[SENDER] Response JSON:", r.json())
        except Exception:
            print("[SENDER] Raw Response:", r.text)
    except Exception as e:
        print("[ERROR] 無法連線到伺服器：", e)


if __name__ == "__main__":
    send_exercise_once()
