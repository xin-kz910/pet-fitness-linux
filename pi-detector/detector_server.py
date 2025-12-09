# detector_server.py
"""
本檔案提供一個本地 API 伺服器（Flask）：
- 前端可 POST /set_user 設定 user_id
- 偵測器可讀取 detector_user.json

啟動方式：
python detector_server.py
"""

from flask import Flask, request, jsonify
import json
import os

USER_FILE = "detector_user.json"

app = Flask(__name__)


def save_user_id(user_id: int):
    data = {"user_id": user_id}
    with open(USER_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f)
    return data


def load_user_id():
    if not os.path.exists(USER_FILE):
        return None

    try:
        with open(USER_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


@app.route("/set_user", methods=["POST"])
def set_user():
    """
    前端登入後會 POST：
    {
        "user_id": 3
    }
    """
    body = request.json
    if not body or "user_id" not in body:
        return jsonify({"success": False, "error": "missing user_id"})

    user_id = int(body["user_id"])
    data = save_user_id(user_id)

    return jsonify({"success": True, "data": data})


@app.route("/get_user", methods=["GET"])
def get_user():
    """偵測器可用來確認目前 user_id 是否已設定"""
    data = load_user_id()
    if not data:
        return jsonify({"success": False, "error": "no user_id found"})
    return jsonify({"success": True, "data": data})


if __name__ == "__main__":
    print("📡 Detector Local API Server 啟動中：http://localhost:5001 ...")
    app.run(host="0.0.0.0", port=5001)
