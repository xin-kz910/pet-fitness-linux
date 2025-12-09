# detector_opencv.py

import cv2
import numpy as np
import time
from sender import send_exercise

MOTION_THRESHOLD = 2_000_000
COOLDOWN_SECONDS = 1.5


def detect_motion_with_webcam():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ 無法開啟攝影機")
        return

    time.sleep(1)
    ret, prev_frame = cap.read()
    prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)

    print("🎬 開始動作偵測（q離開, v切換是否送資料）")
    send_enabled = True
    last_time = 0

    while True:
        ret, frame = cap.read()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        diff = cv2.absdiff(prev_gray, gray)
        motion_level = np.sum(diff)
        now = time.time()

        if motion_level > MOTION_THRESHOLD and (now - last_time > COOLDOWN_SECONDS):
            print(f"⚡ 偵測到運動！ motion={motion_level:.0f}")

            if send_enabled:
                ok = send_exercise(1, source="webcam")
                print("→ 更新結果：", "成功" if ok else "失敗")
            else:
                print("（僅偵測模式，不送資料）")

            last_time = now

        prev_gray = gray

        text = f"motion={motion_level:.0f} send={send_enabled}"
        cv2.putText(frame, text, (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        cv2.imshow("Webcam Motion Detector", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        if key == ord("v"):
            send_enabled = not send_enabled

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    detect_motion_with_webcam()
