# config.py
"""
動作偵測（電腦鏡頭版）共用設定 - 利用 /api/user/server_status 自動判斷 server

這裡只放「不會因為切換伺服器而改變」的設定：
- BASE_URL：Nginx 對外位址
- USER_ID：這台偵測器對應的玩家 ID
"""

# ★ Nginx 對外主機位址（不要加 /serverA）
BASE_URL = "http://10.0.2.15"  # TODO: 換成你們實際的 Nginx IP

# ★ 這台偵測器對應的 user_id（登入之後知道）
USER_ID = 1

# ★ 給偵測器查「目前 server_id」用的 API
#   這支 API 是你剛才貼的 /api/user/server_status
#   因為 DB 是共用的，所以你可以永遠經由 /serverA 來查這個資訊。
SERVER_STATUS_URL = f"{BASE_URL}/serverA/api/user/server_status"

# ★ 用來查 pet 狀態的 API（會依照 server_id 加上不同 prefix）
PET_STATUS_PATH = "/api/pet/status"

# ★ 寵物體力更新 API 路徑（不含 prefix）
UPDATE_PATH = "/api/pet/update"

# ★ server_id -> Nginx prefix 對照表
SERVER_PREFIX_MAP = {
    "A": "/serverA",
    "B": "/serverB",
    "C": "/serverC",
}
