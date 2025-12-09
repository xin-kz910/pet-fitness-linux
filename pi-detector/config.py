"""
動作偵測器（Webcam / Raspberry Pi）共用設定
---------------------------------------------------
本偵測器不硬寫 serverA/serverB/serverC，而是：
1. 先問 /serverA/api/user/server_status → 知道 user 目前在哪台 server（A/B/C）
2. 再依照 server_id 自動組出正確的 /serverX/api/pet/update

此檔案只需設定「不會因為伺服器切換而改變」的部分：
- BASE_URL：Nginx 對外位址（不要加 /serverA）
"""

# ======================================================
# ★ Nginx 對外位址（唯一需要修改的值）
# ======================================================
# EX: "http://192.168.1.20"、"http://10.0.2.15"、"http://203.10.11.25"
BASE_URL = "http://10.0.2.15"  # TODO: 換成實際 Nginx IP


# ======================================================
# ★ 查詢使用者目前所在 server (A/B/C)
#   這支 API 經由任一 server 前綴都能查
#   這裡預設用 /serverA，也可正常查詢（DB 共用）
# ======================================================
SERVER_STATUS_URL = f"{BASE_URL}/serverA/api/user/server_status"


# ======================================================
# ★ server_id -> Nginx prefix 對照表
#   最終組合方式：
#   BASE_URL + prefix + UPDATE_PATH
# ======================================================
SERVER_PREFIX_MAP = {
    "A": "/serverA",
    "B": "/serverB",
    "C": "/serverC",
}


# ======================================================
# ★ 寵物狀態查詢（不含 prefix）
#   實際 URL：BASE_URL + prefix + PET_STATUS_PATH
# ======================================================
PET_STATUS_PATH = "/api/pet/status"


# ======================================================
# ★ 寵物體力更新（不含 prefix）
#   實際 URL：BASE_URL + prefix + UPDATE_PATH
# ======================================================
UPDATE_PATH = "/api/pet/update"
