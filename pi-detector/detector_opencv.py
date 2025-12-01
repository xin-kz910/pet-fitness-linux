import time

import cv2
import numpy as np
import requests

from config import BASE_URL, SERVER_ID, USER_ID, PET_ID

# ------------------------------------------------------------
# 伺服器路徑組合（多伺服器 A / B / C）
# ------------------------------------------------------------

SERVER_PREFIX_MAP = {
    "A": "/serverA",
    "B": "/serverB",
    "C": "/serverC",
}


def build_server_url(path: str) -> str:
    """
    將 BASE_URL + server_id 對應的前綴 + API 路徑組成完整 URL。

    例如：
    - BASE_URL = "http://140.113.1.23"
    - SERVER_ID = "A"
    - path = "/api/pet/update"

    => http://140.113.1.23/serverA/api/pet/update
    """
    prefix = SERVER_PREFIX_MAP.get(SERVER_ID, "/serverA")
    return BASE_URL.rstrip("/") + prefix + path


# 寵物體力更新 API（Pi 回報用）
SERVER_URL = build_server_url("/api/pet/update")


# ------------------------------------------------------------
# 上報函式：Pi 偵測到運動就呼叫這個
# ------------------------------------------------------------

def send_update():
    """
    向後端上報一次運動事件。

    JSON 格式需符合後端 PetUpdateRequest：
    {
      "user_id": 1,
      "pet_id": 1,
      "server_id": "A",
      "exercise_count": 1,
      "source": "raspberry_pi"
    }
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
        # 預期回傳統一格式：{ "success": true/false, "data": ..., "error": ... }
        try:
            resp = r.json()
            print(
                "[UPDATE]",
                "status_code =", r.status_code,
                "success =", resp.get("success"),
            )
        except Exception:
            print("[UPDATE] status_code =", r.status_code, "raw_response =", r.text)
    except Exception as e:
        # 不要讓整個偵測程式因為網路問題直接炸掉
        print("[ERROR] 無法連線到伺服器或解析回應：", e)


# ------------------------------------------------------------
# OpenCV 動作偵測主程式
# ------------------------------------------------------------

def detect_motion():
    """
    使用 OpenCV 的「畫面差分」做簡單動作偵測：

    1. 開啟攝影機
    2. 連續讀取畫面，計算前一幀與目前畫面的差異
    3. 差異（motion_level）超過門檻 => 視為一次運動，呼叫 send_update()
    """

    cap = cv2.VideoCapture(0)   # 0 = 預設攝影機

    if not cap.isOpened():
        print("[ERROR] 無法開啟攝影機（請確認攝影機是否存在或未被佔用）")
        return

    print("正在初始化攝影機 ...")
    time.sleep(1)

    ret, prev_frame = cap.read()
    if not ret:
        print("[ERROR] 無法讀取攝影機畫面")
        cap.release()
        return

    prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)

    print("開始動作偵測！（視窗中按 Q 結束）")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[WARN] 讀取畫面失敗，略過這一幀")
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # 1. 計算畫面差異
        diff = cv2.absdiff(prev_gray, gray)

        # 2. 計算差異量（代表動作大小）
        motion_level = np.sum(diff)

        # 3. 動作門檻值（可依環境調整）
        #    如果太敏感就調大，太鈍就調小
        if motion_level > 2_000_000:
            print("⚡ 偵測到運動！motion_level =", motion_level)
            send_update()
            time.sleep(1)  # 避免在一連串動作中觸發太多次

        prev_gray = gray

        # 顯示畫面（方便測試）
        cv2.imshow("Motion Detector (press Q to quit)", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    print("[INFO] 使用者 ID:", USER_ID, "寵物 ID:", PET_ID, "伺服器:", SERVER_ID)
    print("[INFO] 將上報到：", SERVER_URL)
    detect_motion()

