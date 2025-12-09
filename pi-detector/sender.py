# sender.py

import json
import os
import requests
from typing import Optional, Dict

from config import (
    BASE_URL,
    SERVER_STATUS_URL,
    PET_STATUS_PATH,
    UPDATE_PATH,
    SERVER_PREFIX_MAP,
)

USER_FILE = "detector_user.json"
_detector_config_cache: Optional[Dict] = None


def load_user_id() -> Optional[int]:
    if not os.path.exists(USER_FILE):
        return None
    try:
        with open(USER_FILE, "r") as f:
            data = json.load(f)
            return data.get("user_id")
    except Exception:
        return None


def load_detector_config(force_refresh: bool = False) -> Optional[Dict]:
    global _detector_config_cache

    if _detector_config_cache and not force_refresh:
        return _detector_config_cache

    user_id = load_user_id()
    if not user_id:
        print("[CONFIG][ERROR] 尚未設定 user_id！請先由前端呼叫 /set_user。")
        return None

    # Step 1: 查 server_id
    resp = requests.get(SERVER_STATUS_URL, params={"user_id": user_id}, timeout=3)
    resp_json = resp.json()

    if not resp_json.get("success", False):
        print("[CONFIG][ERROR] server_status 錯誤：", resp_json.get("error"))
        return None

    server_id = resp_json["data"]["server_id"]
    prefix = SERVER_PREFIX_MAP.get(server_id)

    # Step 2: 查 pet_id
    pet_status_url = f"{BASE_URL}{prefix}{PET_STATUS_PATH}"
    resp2 = requests.get(pet_status_url, params={"user_id": user_id}, timeout=3)
    pet_json = resp2.json()

    if not pet_json.get("success", False):
        print("[CONFIG][ERROR] pet_status 錯誤：", pet_json.get("error"))
        return None

    pet_id = pet_json["data"]["pet_id"]

    # Step 3: 組 update_url
    update_url = f"{BASE_URL}{prefix}{UPDATE_PATH}"

    cfg = {
        "user_id": user_id,
        "pet_id": pet_id,
        "server_id": server_id,
        "update_url": update_url,
    }

    _detector_config_cache = cfg
    print("[CONFIG] 偵測器設定：", cfg)
    return cfg


def send_exercise(exercise_count: int = 1, source: str = "webcam") -> bool:
    cfg = load_detector_config()
    if not cfg:
        return False

    payload = {
        "user_id": cfg["user_id"],
        "pet_id": cfg["pet_id"],
        "server_id": cfg["server_id"],
        "exercise_count": exercise_count,
        "source": source,
    }

    print("[SENDER] POST", cfg["update_url"], payload)

    resp = requests.post(cfg["update_url"], json=payload, timeout=3)
    resp_json = resp.json()

    print("[SENDER] 回應：", resp_json)
    return resp_json.get("success", False)
