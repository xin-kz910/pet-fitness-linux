#  就是比狗累 – Just Beagle Lay（運動型虛擬寵物系統）

> 你不動，你的狗比你還累。
> 玩家需要透過真實運動來維持寵物體力，並進行互動、聊天與對戰的多人遊戲系統。

---

# 1. 專案簡介（Overview）

「就是比狗累」是一個整合 **Linux 多伺服器架構、WebSocket 即時通訊、
動作偵測和前後端互動遊戲系統** 的專題作品。

玩家可以：

* 登入系統、選擇伺服器（A/B/C）
* 在大廳看到所有線上玩家的寵物
* 與其他玩家聊天、挑戰 1V1 對戰
* 經營自己的寵物體力（會隨時間下降）
* 透過辨識系統做「真實運動」或是鍵盤操控來恢復體力
* 在排行榜中競爭積分

這是一個結合 **健康、互動與 Linux 架構** 的實作。

---

# 2. 系統特色（Features）

###  遊戲功能

* 多人登入 / 註冊
* 多伺服器大廳（A/B/C 分別獨立）
* 隨機寵物位置顯示
* 即時聊天（群聊＋私訊）
* 寵物體力系統（精神飽滿／疲累／休眠）
* 小恐龍跑酷式 1v1 對戰
* 排行榜（分數自動計算與更新）

###  寵物體力機制

* 體力 0～100
* 每 20 分鐘自動扣 5 點（Cron Job）
* 30 以下進入休眠，功能受限
* 需要透過 **運動偵測** 才能恢復體力

### 運動偵測

* 偵測玩家是否運動
* 偵測成功 → 後端更新寵物體力
* 0～30 需要 2 次運動、30～70 需要 1 次運動
* 讓玩家真正「起身動一動」

---

# 3. 系統架構（Architecture）

前端、Nginx、後端 A/B/C、WebSocket A/B/C、資料庫、Raspberry Pi。

```
[ Browser Frontend ]
         │
         ▼
  Nginx Reverse Proxy
         │
 ┌───────┼───────────┐
 ▼       ▼           ▼
Backend A  Backend B  Backend C
  │         │           │
  ▼         ▼           ▼
 WS A     WS B        WS C
         │
         ▼
     Database

```

### 重點技術

* 前端透過 Nginx 提供靜態頁面與反向代理
* Backend A/B/C 使用 FastAPI，依 server_id 分流玩家
* WS A/B/C 處理大廳同步、聊天、對戰
* PostgreSQL 存玩家、寵物、排行榜
* Raspberry Pi 偵測玩家動作並回報後端

---

# 4. 技術與工具

###  後端 Backend

* Python + FastAPI
* SQLite / PostgreSQL
* Nginx（反向代理）
* Cron Job（體力下降、排行榜更新）
* systemd（常駐服務）

### 即時通訊 WebSocket

* Python websockets
* 即時同步：大廳玩家位置、聊天訊息、對戰狀態

### 前端 Frontend

* HTML / CSS / JavaScript
* 與 API / WebSocket 串接互動

### 動作偵測

* Raspberry Pi OS
* Pi Camera + OpenCV
* HTTP API 傳送偵測結果

---

# 5. 系統功能流程（User Flow）

1. **登入 / 註冊**
2. **選擇伺服器（A/B/C）**
3. **進入大廳** → 看到所有玩家寵物
4. **與玩家互動：聊天 / 挑戰**
5. **寵物體力下降 → 休眠通知**
6. **玩家到鏡頭前做運動**
7. **偵測成功 → 體力恢復**
8. **可繼續對戰、聊天和衝排行榜**

---

# 6. 專案結構（簡化版）

```
pet-fitness-linux/
├── backend/            # 三台後端（A/B/C）
├── ws-server/          # 三台 WebSocket（A/B/C）
├── frontend/           # 前端頁面
├── pi-detector/        # 動作偵測（Raspberry Pi）
├── cron/               # 體力下降 / 排行榜 Job
└── docs/               # API / WS / 架構文件
```

---

# 7. 遇到的挑戰（Challenges）

* 多伺服器之間的 API / WS 架構協同設計
* WebSocket 即時同步延遲與廣播邏輯
* Raspberry Pi 動作偵測整合後端流程
* Cron / systemd 在 Linux 上的服務管理
* 大廳同步、對戰同步的資料一致性

---

# 8. 未來展望（Future Plan）

* 更多運動類型與更準確的偵測
* 寵物進化與裝飾系統
* 多人房間 / 多人對戰模式
* 後台管理介面
* 使用 Docker 讓部署更方便、更穩定

---

# 9. 開發團隊（Contributors）

| 學號        | 姓名  | 分工                       |
| --------- | --- | ------------------------ |
| 112213016 | 陳詩穎 |    |
| 112213018 | 林秀萍 |        |
| 112213025 | 施淯馨 |        |
| 112213034 | 郭家言 | |



