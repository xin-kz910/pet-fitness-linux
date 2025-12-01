import cv2
import numpy as np
import requests
import time

from config import USER_ID, PET_ID, SERVER_ID, BASE_URL

# server_id -> nginx 路徑前綴
SERVER_PREFIX_MAP = {
    "A": "/serverA",
    "B": "/serverB",
    "C": "/serverC",
}


def build_server_url(path: str) -> str:
    """
    path 例如 "/api/pet/update"
    回傳完整 URL，例如 "http://.../serverA/api/pet/update"
    若未使用多伺服器 / Nginx，可直接在 BASE_URL 填完整路徑。
    """
    prefix = SERVER_PREFIX_MAP.get(SERVER_ID, "/serverA")
    return BASE_URL + prefix + path


# 寵物體力更新 API
SERVER_URL = build_server_url("/api/pet/update")


def send_update():
    """
    向後端上報一次運動事件：
    - user_id / pet_id / server_id / exercise_count / source
    - 格式符合後端 PetUpdateRequest 規格
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
        resp = r.json()
        print("[UPDATE] status_code =", r.status_code, "success =", resp.get("success"))
    except Exception as e:
        print("[ERROR] 無法連線到伺服器或解析回應：", e)


def detect_motion():
    """
    使用 OpenCV 做簡單動作偵測：
    - 讀取攝影機連續畫面
    - 計算前一幀與現在畫面差異
    - 差異量超過門檻 -> 視為一次運動，呼叫 send_update()
    """
    cap = cv2.VideoCapture(0)   # 0 = 預設攝影機

    if not cap.isOpened():
        print("[ERROR] 無法開啟攝影機")
        return

    print("正在初始化攝影機 ...")
    time.sleep(1)

    ret, prev_frame = cap.read()
    if not ret:
        print("[ERROR] 無法讀取攝影機畫面")
        cap.release()
        return

    prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)

    print("開始動作偵測！（按 Q 結束）")

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

        # 3. 動作門檻值（可依實際環境調整）
        if motion_level > 2_000_000:
            print("⚡ 偵測到運動！motion_level =", motion_level)
            send_update()
            time.sleep(1)  # 避免連續觸發過多

        prev_gray = gray

        # 顯示畫面（測試用）
        cv2.imshow("Motion Detector", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    detect_motion()
