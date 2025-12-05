# ws-server/wsC/main.py

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Tuple, List, Set
from dataclasses import dataclass, field
import time
import json
import random  # 用來產生大廳隨機座標


# ---------------------------------------------------------
# 簡單 log 函式：之後都用這個印，方便在 demo 給老師看
# ---------------------------------------------------------
def log(prefix: str, message: str) -> None:
    """
    prefix：分類，例如 CONNECT / CHAT / BATTLE_UPDATE
    message：想印的內容
    """
    print(f"[wsC][{prefix}] {message}")


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
    """管理所有 WebSocket 連線 + 大廳 + 對戰房 + 聊天許可"""

    def __init__(self) -> None:
        # 線上使用者: (server_id, user_id) -> WebSocket
        self.active_connections: Dict[UserKey, WebSocket] = {}
        # 每個 server 的大廳成員: server_id -> set(user_id)
        self.lobby_users: Dict[str, Set[int]] = {}
        # 大廳玩家詳細資訊（含寵物 / 座標）：server_id -> { user_id -> info_dict }
        self.lobby_player_states: Dict[str, Dict[int, dict]] = {}

        # 對戰房間: battle_id -> BattleRoom
        self.battles: Dict[str, BattleRoom] = {}

        # 已互相同意聊天的配對：例如 (1, 2) 代表 user1 與 user2 可以互傳訊息
        self.chat_approved_pairs: Set[Tuple[int, int]] = set()

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
        # 把大廳玩家狀態也移除
        if server_id in self.lobby_player_states:
            self.lobby_player_states[server_id].pop(user_id, None)
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
            try:
                await ws.send_text(json.dumps(msg, ensure_ascii=False))
            except RuntimeError:
                log("SEND_ERROR", f"server={server_id}, user_id={to_user_id} 傳送失敗，略過")

    async def broadcast_in_server(
        self,
        server_id: str,
        msg: dict,
        exclude: int | None = None,
    ) -> None:
        """對同一個 server 的所有人廣播（可排除某個 user_id）"""
        for (sid, uid), ws in list(self.active_connections.items()):
            if sid != server_id:
                continue
            if exclude is not None and uid == exclude:
                continue
            try:
                await ws.send_text(json.dumps(msg, ensure_ascii=False))
            except RuntimeError:
                # 有人網路壞掉就先忽略
                log("SEND_ERROR", f"server={sid}, user_id={uid} 傳送失敗，略過")
                continue

    # === 大廳玩家資訊相關（寵物 / 座標 / 體力） ===
    def upsert_lobby_player(self, server_id: str, user_id: int, info: dict) -> None:
        """更新或新增大廳玩家資訊（含寵物 / energy / 座標）"""
        if server_id not in self.lobby_player_states:
            self.lobby_player_states[server_id] = {}
        info["user_id"] = user_id
        self.lobby_player_states[server_id][user_id] = info

    def get_lobby_players(self, server_id: str) -> List[dict]:
        """取得某個 server 的所有玩家詳細資訊（list 形式，依 user_id 排序）"""
        server_players = self.lobby_player_states.get(server_id, {})
        return [server_players[uid] for uid in sorted(server_players.keys())]

    def get_player_state(self, server_id: str, user_id: int) -> dict | None:
        """取得單一玩家的狀態（可能為 None）"""
        return self.lobby_player_states.get(server_id, {}).get(user_id)

    def get_player_energy(self, server_id: str, user_id: int) -> int | None:
        """取得玩家體力（若沒紀錄則回 None）"""
        state = self.get_player_state(server_id, user_id)
        if not state:
            return None
        return int(state.get("energy", 0))

    # === 聊天許可相關 ===
    def approve_chat_pair(self, user1_id: int, user2_id: int) -> None:
        """記錄兩個使用者之間的聊天已被同意"""
        pair = tuple(sorted((user1_id, user2_id)))
        self.chat_approved_pairs.add(pair)
        log("CHAT_APPROVED", f"pair={pair} 已允許聊天")

    def is_chat_approved(self, from_user_id: int, to_user_id: int) -> bool:
        """檢查兩個使用者之間是否已互相同意聊天"""
        pair = tuple(sorted((from_user_id, to_user_id)))
        return pair in self.chat_approved_pairs

    # === 對戰相關輔助 ===
    def create_battle(self, server_id: str, player1_id: int, player2_id: int) -> BattleRoom:
        """建立一個新的對戰房間，回傳 BattleRoom"""
        ts = int(time.time() * 1000)
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

    def find_battle_by_user(self, server_id: str, user_id: int) -> BattleRoom | None:
        """找到某個使用者目前所在的對戰房（若有）"""
        for room in self.battles.values():
            if room.server_id != server_id:
                continue
            if user_id in (room.player1_id, room.player2_id):
                return room
        return None


manager = ConnectionManager()

# -------------------------------------------------------------------
# 事件處理：join_lobby / pet_state_update / chat_* / battle_*
# -------------------------------------------------------------------


async def handle_join_lobby(message: dict, websocket: WebSocket) -> None:
    """
    處理玩家進入大廳
    """
    server_id = message.get("server_id", "C")
    user_id = int(message.get("user_id"))
    payload = message.get("payload") or {}

    # 記錄連線與大廳
    manager.connect(server_id, user_id, websocket)

    # 取得玩家資訊（若缺少就用預設 / 隨機）
    display_name = payload.get("display_name") or f"Player{user_id}"
    pet_id = payload.get("pet_id") or 0
    pet_name = payload.get("pet_name") or "MyPet"
    energy = int(payload.get("energy", 100))
    status = payload.get("status") or "ACTIVE"

    x = payload.get("x")
    y = payload.get("y")
    if x is None or y is None:
        x = random.randint(0, 1000)
        y = random.randint(0, 600)

    player_info = {
        "display_name": display_name,
        "pet_id": int(pet_id),
        "pet_name": pet_name,
        "energy": energy,
        "status": status,
        "x": x,
        "y": y,
    }
    manager.upsert_lobby_player(server_id, user_id, player_info)

    # 回傳目前大廳所有在線玩家的完整資訊
    players = manager.get_lobby_players(server_id)
    log(
        "JOIN_LOBBY",
        f"server={server_id}, user_id={user_id}, players={players}",
    )

    lobby_state_msg = {
        "type": "lobby_state",
        "server_id": server_id,
        "user_id": user_id,
        "payload": {
            "players": players,
        },
    }
    await manager.send_json(server_id, user_id, lobby_state_msg)

    # 廣播：有新玩家加入（只傳新玩家 info）
    player_joined_msg = {
        "type": "player_joined",
        "server_id": server_id,
        "user_id": user_id,
        "payload": {
            "player": {
                "user_id": user_id,
                "display_name": display_name,
                "pet_id": int(pet_id),
                "pet_name": pet_name,
                "energy": energy,
                "status": status,
                "x": x,
                "y": y,
            }
        },
    }
    await manager.broadcast_in_server(server_id, player_joined_msg, exclude=user_id)


# -------------------------
# 寵物狀態更新事件
# -------------------------


async def handle_pet_state_update(message: dict) -> None:
    """
    更新單一玩家寵物狀態（例如：體力下降 / 運動回滿）
    """
    server_id = message.get("server_id", "C")
    user_id = int(message.get("user_id"))
    payload = message.get("payload") or {}

    state = manager.get_player_state(server_id, user_id) or {}
    if "energy" in payload:
        state["energy"] = int(payload["energy"])
    if "status" in payload:
        state["status"] = str(payload["status"])
    if "x" in payload:
        state["x"] = int(payload["x"])
    if "y" in payload:
        state["y"] = int(payload["y"])

    manager.upsert_lobby_player(server_id, user_id, state)

    log(
        "PET_STATE_UPDATE",
        f"server={server_id}, user_id={user_id}, state={state}",
    )

    msg = {
        "type": "pet_state_update",
        "server_id": server_id,
        "user_id": user_id,
        "payload": {
            "player": state,
        },
    }
    await manager.broadcast_in_server(server_id, msg)


# -------------------------
# 聊天相關事件
# -------------------------


async def handle_chat_request(message: dict) -> None:
    """
    第一次聊天的請求
    """
    server_id = message.get("server_id", "C")
    from_user_id = int(message.get("user_id"))
    payload = message.get("payload") or {}

    to_user_id = payload.get("to_user_id")
    if to_user_id is None:
        log("CHAT_REQ_ERROR", "缺少 to_user_id，忽略 chat_request")
        return
    to_user_id = int(to_user_id)

    log(
        "CHAT_REQUEST",
        f"server={server_id}, from={from_user_id}, to={to_user_id}",
    )

    msg = {
        "type": "chat_request",
        "server_id": server_id,
        "user_id": from_user_id,
        "payload": {
            "from_user_id": from_user_id,
            "to_user_id": to_user_id,
        },
    }
    await manager.send_json(server_id, to_user_id, msg)


async def handle_chat_request_accept(message: dict) -> None:
    """
    對方接受聊天請求
    """
    server_id = message.get("server_id", "C")
    accept_user_id = int(message.get("user_id"))
    payload = message.get("payload") or {}
    from_user_id = payload.get("from_user_id")

    if from_user_id is None:
        log("CHAT_ACCEPT_ERROR", "缺少 from_user_id，忽略 chat_request_accept")
        return
    from_user_id = int(from_user_id)

    manager.approve_chat_pair(accept_user_id, from_user_id)

    log(
        "CHAT_REQUEST_ACCEPT",
        f"server={server_id}, from={from_user_id}, accepted_by={accept_user_id}",
    )

    for uid in (accept_user_id, from_user_id):
        msg = {
            "type": "chat_approved",
            "server_id": server_id,
            "user_id": uid,
            "payload": {
                "user_id_1": from_user_id,
                "user_id_2": accept_user_id,
            },
        }
        await manager.send_json(server_id, uid, msg)


async def handle_chat_message(message: dict) -> None:
    """
    一對一聊天訊息
    - 體力 <= 30（休眠） → 不可聊天
    - 必須先互相同意
    """
    server_id = message.get("server_id", "C")
    user_id = int(message.get("user_id"))
    payload = message.get("payload") or {}

    content = str(payload.get("content", ""))
    to_user_id = payload.get("to_user_id")

    if to_user_id is None:
        log("CHAT_ERROR", "缺少 to_user_id，忽略此訊息")
        return

    to_user_id = int(to_user_id)

    # 體力檢查
    energy = manager.get_player_energy(server_id, user_id)
    if energy is not None and energy <= 30:
        log(
            "CHAT_BLOCKED_ENERGY",
            f"server={server_id}, from={user_id}, to={to_user_id}, energy={energy} (休眠，禁止聊天)",
        )
        error_msg = {
            "type": "chat_not_allowed",
            "server_id": server_id,
            "user_id": user_id,
            "payload": {
                "reason": "LOW_ENERGY",
                "message": "您的小寵物正在休眠狀態，無法聊天。",
            },
        }
        await manager.send_json(server_id, user_id, error_msg)
        return

    # 是否已同意聊天
    if not manager.is_chat_approved(user_id, to_user_id):
        log(
            "CHAT_BLOCKED",
            f"server={server_id}, from={user_id}, to={to_user_id} 尚未同意聊天，拒絕傳送",
        )
        error_msg = {
            "type": "chat_not_allowed",
            "server_id": server_id,
            "user_id": user_id,
            "payload": {
                "reason": "CHAT_NOT_APPROVED",
                "message": "對方尚未同意與你聊天",
            },
        }
        await manager.send_json(server_id, user_id, error_msg)
        return

    log(
        "CHAT",
        f"server={server_id}, from={user_id}, to={to_user_id}, content={content!r}",
    )

    chat_msg = {
        "type": "chat_message",
        "server_id": server_id,
        "user_id": user_id,
        "payload": {
            "from_user_id": user_id,
            "to_user_id": to_user_id,
            "content": content,
        },
    }

    await manager.send_json(server_id, user_id, chat_msg)
    await manager.send_json(server_id, to_user_id, chat_msg)


# -------------------------
# 對戰相關事件
# -------------------------


async def handle_battle_invite(message: dict) -> None:
    """
    A 玩家邀請 B 玩家對戰
    - 邀請者體力需 >= 70
    """
    server_id = message.get("server_id", "C")
    user_id = int(message.get("user_id"))  # 邀請者
    payload = message.get("payload") or {}
    to_user_id = int(payload.get("to_user_id"))

    inviter_energy = manager.get_player_energy(server_id, user_id)
    if inviter_energy is not None and inviter_energy < 70:
        log(
            "BATTLE_INVITE_BLOCKED_ENERGY",
            f"server={server_id}, inviter={user_id}, energy={inviter_energy} (<70，不可對戰)",
        )
        msg = {
            "type": "battle_not_allowed",
            "server_id": server_id,
            "user_id": user_id,
            "payload": {
                "reason": "INVITER_LOW_ENERGY",
                "message": "您的小寵物疲累或休眠，無法發起對戰。",
            },
        }
        await manager.send_json(server_id, user_id, msg)
        return

    log("BATTLE_INVITE", f"server={server_id}, from={user_id}, to={to_user_id}")

    invite_msg = {
        "type": "battle_invite",
        "server_id": server_id,
        "user_id": user_id,
        "payload": {
            "from_user_id": user_id,
            "to_user_id": to_user_id,
        },
    }
    await manager.send_json(server_id, to_user_id, invite_msg)


async def handle_battle_accept(message: dict) -> None:
    """
    B 玩家接受邀請，建立對戰房間並通知雙方 battle_start
    - 雙方體力都需 >= 70
    """
    server_id = message.get("server_id", "C")
    accept_user_id = int(message.get("user_id"))  # 接受邀請的人 (B)
    payload = message.get("payload") or {}
    from_user_id = int(payload.get("from_user_id"))  # 發出邀請的人 (A)

    p1_energy = manager.get_player_energy(server_id, from_user_id)
    p2_energy = manager.get_player_energy(server_id, accept_user_id)

    if (p1_energy is not None and p1_energy < 70) or (p2_energy is not None and p2_energy < 70):
        log(
            "BATTLE_ACCEPT_BLOCKED_ENERGY",
            f"server={server_id}, A(user={from_user_id}, energy={p1_energy}), "
            f"B(user={accept_user_id}, energy={p2_energy}) 中有人 <70，不可對戰",
        )

        msg_a = {
            "type": "battle_not_allowed",
            "server_id": server_id,
            "user_id": from_user_id,
            "payload": {
                "reason": "LOW_ENERGY",
                "message": "雙方必須保持精神飽滿（體力 ≥ 70）才可以開始對戰。",
            },
        }
        msg_b = {
            "type": "battle_not_allowed",
            "server_id": server_id,
            "user_id": accept_user_id,
            "payload": {
                "reason": "LOW_ENERGY",
                "message": "雙方必須保持精神飽滿（體力 ≥ 70）才可以開始對戰。",
            },
        }
        await manager.send_json(server_id, from_user_id, msg_a)
        await manager.send_json(server_id, accept_user_id, msg_b)
        return

    room = manager.create_battle(server_id, from_user_id, accept_user_id)

    log(
        "BATTLE_ACCEPT",
        f"server={server_id}, from={from_user_id}, accepted_by={accept_user_id}, "
        f"battle_id={room.battle_id}",
    )

    battle_start_payload = {
        "battle_id": room.battle_id,
        "player1_id": room.player1_id,
        "player2_id": room.player2_id,
    }

    for pid in (room.player1_id, room.player2_id):
        msg = {
            "type": "battle_start",
            "server_id": server_id,
            "user_id": pid,
            "payload": battle_start_payload,
        }
        await manager.send_json(server_id, pid, msg)


async def handle_battle_update(message: dict) -> None:
    """
    對戰過程中更新分數 / 狀態（雙方都收到）
    """
    server_id = message.get("server_id", "C")
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
            "scores": room.scores,
            "state": state,
        },
    }
    await manager.send_json(server_id, room.player1_id, update_msg)
    await manager.send_json(server_id, room.player2_id, update_msg)


async def handle_battle_result(message: dict) -> None:
    """對戰結束，廣播結果並清掉房間"""
    server_id = message.get("server_id", "C")
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


async def handle_battle_disconnect(server_id: str, user_id: int) -> None:
    """
    對戰中有人斷線時：
    - 自動判定另一方為贏家
    - 廣播 battle_result
    - 清除 battle_room
    """
    room = manager.find_battle_by_user(server_id, user_id)
    if room is None:
        return

    if user_id == room.player1_id:
        winner_user_id = room.player2_id
    else:
        winner_user_id = room.player1_id

    player1_score = room.scores.get(room.player1_id, 0)
    player2_score = room.scores.get(room.player2_id, 0)

    log(
        "BATTLE_DISCONNECT",
        f"server={server_id}, disconnect_user={user_id}, "
        f"winner={winner_user_id}, battle_id={room.battle_id}",
    )

    result_msg = {
        "type": "battle_result",
        "server_id": server_id,
        "user_id": winner_user_id,
        "payload": {
            "battle_id": room.battle_id,
            "winner_user_id": winner_user_id,
            "player1_id": room.player1_id,
            "player2_id": room.player2_id,
            "player1_score": player1_score,
            "player2_score": player2_score,
        },
    }

    await manager.send_json(server_id, room.player1_id, result_msg)
    await manager.send_json(server_id, room.player2_id, result_msg)

    manager.finish_battle(room.battle_id)


# -------------------------------------------------------------------
# FastAPI 路由
# -------------------------------------------------------------------

@app.get("/")
async def health_check():
    """健康檢查"""
    log("HEALTH_CHECK", "收到 / 請求")
    return {"message": "wsC server running", "server_id": "C"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket 入口：
    - 先 accept
    - 收到第一包 join_lobby 才會把使用者加入大廳
    - 一條連線只能代表一個 user_id（防止冒名送訊息）
    """
    await websocket.accept()
    server_id = "C"
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
            server_id = message.get("server_id", "C")

            # 從訊息裡先讀出 user_id（可能是錯的或被亂改）
            msg_user_id_raw = message.get("user_id")
            msg_user_id: int | None = None
            if msg_user_id_raw is not None:
                try:
                    msg_user_id = int(msg_user_id_raw)
                except (TypeError, ValueError):
                    msg_user_id = None

            # ---------- 第一階段：處理 join_lobby ----------
            if msg_type == "join_lobby":
                if msg_user_id is None:
                    log("JOIN_LOBBY_ERROR", "join_lobby 缺少有效 user_id，忽略")
                    continue

                if user_id is None:
                    user_id = msg_user_id
                    log("WS_BIND_USER", f"這條連線綁定為 user_id={user_id}")
                else:
                    if msg_user_id != user_id:
                        log(
                            "JOIN_LOBBY_IMPERSONATE",
                            f"連線實際 user_id={user_id}，但 join_lobby 帶 user_id={msg_user_id}，忽略",
                        )
                        continue

                message["user_id"] = user_id
                await handle_join_lobby(message, websocket)
                continue

            # ---------- 第二階段：其他事件，都必須已經綁定 user_id ----------
            if user_id is None:
                log("WS_NO_USER", f"尚未 join_lobby 的連線收到 {msg_type}，忽略")
                continue

            if msg_user_id is not None and msg_user_id != user_id:
                log(
                    "WS_IMPERSONATE",
                    f"連線實際 user_id={user_id}，但訊息帶 user_id={msg_user_id}，拒絕",
                )
                continue

            message["user_id"] = user_id

            if msg_type == "pet_state_update":
                await handle_pet_state_update(message)
            elif msg_type == "chat_request":
                await handle_chat_request(message)
            elif msg_type == "chat_request_accept":
                await handle_chat_request_accept(message)
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
        if user_id is not None:
            await handle_battle_disconnect(server_id, user_id)

            manager.disconnect(server_id, user_id)
            log("WS_DISCONNECT", f"server={server_id}, user_id={user_id} 斷線")

            player_left_msg = {
                "type": "player_left",
                "server_id": server_id,
                "user_id": user_id,
                "payload": {},
            }
            await manager.broadcast_in_server(server_id, player_left_msg, exclude=user_id)

