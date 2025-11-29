# ws-server/wsB/main.py

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Tuple, List, Set
from dataclasses import dataclass, field
import time
import json

# ---------------------------------------------------------
# 簡單 log 函式：之後都用這個印，方便在 demo 給老師看
# ---------------------------------------------------------
def log(prefix: str, message: str) -> None:
    """
    prefix：分類，例如 CONNECT / CHAT / BATTLE_UPDATE
    message：想印的內容
    """
    print(f"[wsB][{prefix}] {message}")


app = FastAPI()

# 先開 CORS，之後前端要連線會比較方便
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# (server_id, user_id) 當 key
UserKey = Tuple[str, int]


@dataclass
class BattleRoom:
    """一個對戰房間的狀態（放在記憶體）"""
    battle_id: str
    server_id: str
    player1_id: int
    player2_id: int
    scores: Dict[int, int] = field(default_factory=dict)
    state: str = "waiting"  # waiting / running / finished


class ConnectionManager:
    """管理所有 WebSocket 連線 + 大廳 + 對戰房"""

    def __init__(self) -> None:
        # 線上使用者: (server_id, user_id) -> WebSocket
        self.active_connections: Dict[UserKey, WebSocket] = {}
        # 每個 server 的大廳成員: server_id -> set(user_id)
        self.lobby_users: Dict[str, Set[int]] = {}
        # 對戰房間: battle_id -> BattleRoom
        self.battles: Dict[str, BattleRoom] = {}

    # === 連線 / 大廳 ===
    def connect(self, server_id: str, user_id: int, websocket: WebSocket) -> None:
        """記錄某個使用者已連線並加入大廳"""
        key: UserKey = (server_id, user_id)
        self.active_connections[key] = websocket
        if server_id not in self.lobby_users:
            self.lobby_users[server_id] = set()
        self.lobby_users[server_id].add(user_id)
        log("CONNECT", f"server={server_id}, user_id={user_id} 加入連線與大廳")

    def disconnect(self, server_id: str, user_id: int) -> None:
        """斷線時，把連線與大廳紀錄清掉"""
        key: UserKey = (server_id, user_id)
        self.active_connections.pop(key, None)
        if server_id in self.lobby_users:
            self.lobby_users[server_id].discard(user_id)
        log("DISCONNECT", f"server={server_id}, user_id={user_id} 離線並退出大廳")

    def get_online_users(self, server_id: str) -> List[int]:
        """回傳該 server 大廳裡目前所有 user_id（排序過）"""
        return sorted(self.lobby_users.get(server_id, set()))

    def get_ws(self, server_id: str, user_id: int) -> WebSocket | None:
        """拿到某個使用者的 WebSocket"""
        return self.active_connections.get((server_id, user_id))

    async def send_json(self, server_id: str, to_user_id: int, msg: dict) -> None:
        """對單一使用者送一個 JSON 訊息"""
        ws = self.get_ws(server_id, to_user_id)
        if ws is not None:
            await ws.send_text(json.dumps(msg, ensure_ascii=False))

    async def broadcast_in_server(
        self,
        server_id: str,
        msg: dict,
        exclude: int | None = None,
    ) -> None:
        """對同一個 server 的所有人廣播（可排除某個 user_id）"""
        for (sid, uid), ws in self.active_connections.items():
            if sid != server_id:
                continue
            if exclude is not None and uid == exclude:
                continue
            try:
                await ws.send_text(json.dumps(msg, ensure_ascii=False))
            except RuntimeError:
                # 有人網路壞掉就先忽略
                log("SEND_ERROR", f"server={sid}, user_id={uid} 傳送失敗，略過")
                pass

    # === 對戰相關輔助 ===
    def create_battle(self, server_id: str, player1_id: int, player2_id: int) -> BattleRoom:
        """建立一個新的對戰房間，回傳 BattleRoom"""
        ts = int(time.time() * 1000)
        # battle_id 例子: "123_456_20251129000000"
        battle_id = f"{min(player1_id, player2_id)}_{max(player1_id, player2_id)}_{ts}"
        room = BattleRoom(
            battle_id=battle_id,
            server_id=server_id,
            player1_id=player1_id,
            player2_id=player2_id,
            scores={player1_id: 0, player2_id: 0},
        )
        self.battles[battle_id] = room
        log(
            "BATTLE_CREATE",
            f"server={server_id}, battle_id={battle_id}, "
            f"player1={player1_id}, player2={player2_id}",
        )
        return room

    def get_battle(self, battle_id: str) -> BattleRoom | None:
        return self.battles.get(battle_id)

    def finish_battle(self, battle_id: str) -> None:
        self.battles.pop(battle_id, None)
        log("BATTLE_FINISH", f"battle_id={battle_id} 已移除")


manager = ConnectionManager()

# -------------------------------------------------------------------
# 事件處理：join_lobby / chat_message / battle_*
# -------------------------------------------------------------------


async def handle_join_lobby(message: dict, websocket: WebSocket) -> None:
    """處理玩家進入大廳"""
    server_id = message.get("server_id", "B")
    user_id = int(message.get("user_id"))

    # 記錄連線與大廳
    manager.connect(server_id, user_id, websocket)

    # 回傳目前大廳所有在線 user
    online_users = manager.get_online_users(server_id)
    log("JOIN_LOBBY", f"server={server_id}, user_id={user_id}, online_users={online_users}")

    lobby_state_msg = {
        "type": "lobby_state",
        "server_id": server_id,
        "user_id": user_id,
        "payload": {
            "online_users": online_users,
        },
    }
    await manager.send_json(server_id, user_id, lobby_state_msg)

    # 廣播：有新玩家加入
    player_joined_msg = {
        "type": "player_joined",
        "server_id": server_id,
        "user_id": user_id,
        "payload": {},
    }
    await manager.broadcast_in_server(server_id, player_joined_msg, exclude=user_id)


async def handle_chat_message(message: dict) -> None:
    """處理聊天訊息（廣播給同一個 server 的所有玩家）"""
    server_id = message.get("server_id", "B")
    user_id = int(message.get("user_id"))
    payload = message.get("payload") or {}
    content = str(payload.get("content", ""))

    log("CHAT", f"server={server_id}, from={user_id}, content={content!r}")

    broadcast_msg = {
        "type": "chat_message",
        "server_id": server_id,
        "user_id": user_id,
        "payload": {"content": content},
    }
    await manager.broadcast_in_server(server_id, broadcast_msg)


async def handle_battle_invite(message: dict) -> None:
    """A 玩家邀請 B 玩家對戰"""
    server_id = message.get("server_id", "B")
    user_id = int(message.get("user_id"))
    payload = message.get("payload") or {}
    target_user_id = int(payload.get("target_user_id"))

    log("BATTLE_INVITE", f"server={server_id}, from={user_id}, to={target_user_id}")

    invite_msg = {
        "type": "battle_invite",
        "server_id": server_id,
        "user_id": user_id,
        "payload": {
            "from_user_id": user_id,
        },
    }
    await manager.send_json(server_id, target_user_id, invite_msg)


async def handle_battle_accept(message: dict) -> None:
    """B 玩家接受邀請，建立對戰房間並通知雙方 battle_start"""
    server_id = message.get("server_id", "B")
    user_id = int(message.get("user_id"))  # 接受邀請的人
    payload = message.get("payload") or {}
    from_user_id = int(payload.get("from_user_id"))  # 發出邀請的人

    room = manager.create_battle(server_id, from_user_id, user_id)

    log(
        "BATTLE_ACCEPT",
        f"server={server_id}, from={from_user_id}, accepted_by={user_id}, "
        f"battle_id={room.battle_id}",
    )

    battle_start_payload = {
        "battle_id": room.battle_id,
        "player1_id": room.player1_id,
        "player2_id": room.player2_id,
    }

    # 通知兩位玩家
    for pid in (room.player1_id, room.player2_id):
        msg = {
            "type": "battle_start",
            "server_id": server_id,
            "user_id": pid,
            "payload": battle_start_payload,
        }
        await manager.send_json(server_id, pid, msg)


async def handle_battle_update(message: dict) -> None:
    """對戰過程中更新分數 / 狀態（雙方都收到）"""
    server_id = message.get("server_id", "B")
    user_id = int(message.get("user_id"))
    payload = message.get("payload") or {}
    battle_id = str(payload.get("battle_id"))
    score = int(payload.get("score", 0))
    state = str(payload.get("state", "running"))

    room = manager.get_battle(battle_id)
    if room is None:
        log("BATTLE_UPDATE", f"battle_id={battle_id} 不存在，略過")
        return

    room.scores[user_id] = score
    room.state = state

    log(
        "BATTLE_UPDATE",
        f"battle_id={battle_id}, user_id={user_id}, score={score}, state={state}",
    )

    update_msg = {
        "type": "battle_update",
        "server_id": server_id,
        "user_id": user_id,
        "payload": {
            "battle_id": battle_id,
            "user_id": user_id,
            "score": score,
            "state": state,
        },
    }
    await manager.send_json(server_id, room.player1_id, update_msg)
    await manager.send_json(server_id, room.player2_id, update_msg)


async def handle_battle_result(message: dict) -> None:
    """對戰結束，廣播結果並清掉房間"""
    server_id = message.get("server_id", "B")
    user_id = int(message.get("user_id"))
    payload = message.get("payload") or {}
    battle_id = str(payload.get("battle_id"))
    winner_user_id = int(payload.get("winner_user_id"))
    player1_score = int(payload.get("player1_score", 0))
    player2_score = int(payload.get("player2_score", 0))

    room = manager.get_battle(battle_id)
    if room is None:
        log("BATTLE_RESULT", f"battle_id={battle_id} 不存在，略過")
        return

    log(
        "BATTLE_RESULT",
        f"battle_id={battle_id}, winner={winner_user_id}, "
        f"p1={room.player1_id} score={player1_score}, "
        f"p2={room.player2_id} score={player2_score}",
    )

    result_msg = {
        "type": "battle_result",
        "server_id": server_id,
        "user_id": user_id,
        "payload": {
            "battle_id": battle_id,
            "winner_user_id": winner_user_id,
            "player1_id": room.player1_id,
            "player2_id": room.player2_id,
            "player1_score": player1_score,
            "player2_score": player2_score,
        },
    }
    await manager.send_json(server_id, room.player1_id, result_msg)
    await manager.send_json(server_id, room.player2_id, result_msg)

    manager.finish_battle(battle_id)


# -------------------------------------------------------------------
# FastAPI 路由
# -------------------------------------------------------------------

@app.get("/")
async def health_check():
    """健康檢查：你現在看到的 JSON 就是這個"""
    log("HEALTH_CHECK", "收到 / 請求")
    return {"message": "wsB server running", "server_id": "B"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket 入口：
    - 先 accept
    - 收到第一包 join_lobby 才會把使用者加入大廳
    """
    await websocket.accept()
    server_id = "B"
    user_id: int | None = None
    log("WS_ACCEPT", "有新的 WebSocket 連線進來")

    try:
        while True:
            raw = await websocket.receive_text()
            log("WS_RECV_RAW", raw)

            try:
                message = json.loads(raw)
            except json.JSONDecodeError:
                log("WS_ERROR", f"收到非 JSON：{raw!r}")
                continue

            msg_type = message.get("type")
            server_id = message.get("server_id", "B")

            if "user_id" in message:
                try:
                    user_id = int(message["user_id"])
                except (TypeError, ValueError):
                    user_id = None

            # 根據 type 分派到不同 handler
            if msg_type == "join_lobby":
                if user_id is None:
                    log("JOIN_LOBBY_ERROR", "缺少有效 user_id，忽略")
                    continue
                await handle_join_lobby(message, websocket)
            elif msg_type == "chat_message":
                await handle_chat_message(message)
            elif msg_type == "battle_invite":
                await handle_battle_invite(message)
            elif msg_type == "battle_accept":
                await handle_battle_accept(message)
            elif msg_type == "battle_update":
                await handle_battle_update(message)
            elif msg_type == "battle_result":
                await handle_battle_result(message)
            else:
                log("WS_UNKNOWN_TYPE", f"未知事件 type={msg_type!r}，略過")

    except WebSocketDisconnect:
        # 斷線時把人從大廳移除
        if user_id is not None:
            manager.disconnect(server_id, user_id)
            log("WS_DISCONNECT", f"server={server_id}, user_id={user_id} 斷線")

