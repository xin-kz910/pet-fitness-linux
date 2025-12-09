# detector_opencv.py
"""
使用「電腦鏡頭」的動作偵測程式（Windows / Ubuntu 都可）

流程：
- 啟動攝影機
- 連續兩幀做差分，計算 motion_level
- 超過門檻就視為有運動，呼叫 send_exercise()

快捷鍵：
- q：離開程式
- v：切換「是否真的送資料」模式（方便只測畫面）
"""

import cv2
import numpy as np
import time

from sender import send_exercise


MOTION_THRESHOLD = 2_000_000  # 動作門檻值，太敏感就調大
COOLDOWN_SECONDS = 1.5        # 觸發一次後 N 秒內不再重複觸發


def detect_motion_with_webcam():
    cap = cv2.VideoCapture(0)  # 0 = 預設鏡頭

    if not cap.isOpened():
        print("❌ 開啟攝影機失敗，請確認鏡頭是否存在 / 沒被其他程式占用。")
        return

    print("正在初始化攝影機 ...")
    time.sleep(1)

    ret, prev_frame = cap.read()
    if not ret:
        print("❌ 無法讀取第一幀畫面，結束。")
        cap.release()
        return

    prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)

    print("✅ 開始動作偵測！（按 q 結束，按 v 切換是否送資料）")

    last_trigger_time = 0.0
    send_enabled = True

    while True:
        ret, frame = cap.read()
        if not ret:
            print("⚠ 無法取得畫面，略過這一幀 ...")
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # 1. 計算畫面差分
        diff = cv2.absdiff(prev_gray, gray)

        # 2. 計算差異量（越大代表動作越大）
        motion_level = float(np.sum(diff))

        # 3. 判斷是否觸發運動事件
        now = time.time()
        if motion_level > MOTION_THRESHOLD and (now - last_trigger_time) > COOLDOWN_SECONDS:
            print(f"⚡ 偵測到運動！motion_level = {motion_level:.0f}")

            if send_enabled:
                ok = send_exercise(exercise_count=1, source="webcam")
                if ok:
                    print("✅ 已通知後端更新寵物體力。")
                else:
                    print("❌ 通知後端失敗（可稍後再試）。")
            else:
                print("（目前處於僅偵測模式，不送資料）")

            last_trigger_time = now

        prev_gray = gray

        # 4. 顯示畫面與狀態
        status_text = f"motion={motion_level:.0f} send={'ON' if send_enabled else 'OFF'}"
        cv2.putText(
            frame,
            status_text,
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2,
        )

        cv2.imshow("Motion Detector (Webcam)", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            print("👋 收到 q，結束程式。")
            break
        elif key == ord("v"):
            send_enabled = not send_enabled
            print(f"🔁 切換模式：送資料 = {send_enabled}")

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    detect_motion_with_webcam()
