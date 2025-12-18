# 就是比狗累 – Just Beagle Lay（運動型虛擬寵物系統）
## Concept Development
本專題旨在設計並實作一個運動型虛擬寵物系統（Virtual Pet Fitness System）。
使用者可透過網頁登入系統，擁有一隻專屬的虛擬寵物，並透過互動、遊戲或動作行為影響寵物的體力、積分與成長狀態。

系統強調：
- 多使用者同時在線
- 即時狀態同步
- Linux 環境下的伺服器與服務整合

透過本專題，我們實際應用 Linux 系統管理課程中所學的伺服器架構、網路服務與背景任務概念。
## Implementation Resources
- Operating System: Linux (Virtual Machine)
- Web Server: Nginx
- Backend Framework: FastAPI (Python)
- Real-time Communication: WebSocket
- Database: PostgreSQL
- Frontend: HTML / CSS / JavaScript
- Image Processing: Mediapipe
- Camera Device: Built-in Camera
- Scheduling / Timer: systemd timer
- Version Control: Git / GitHub
## Existing Library/Software
本專題使用以下現有函式庫與軟體工具：
- FastAPI – 建立後端 API 服務
- Uvicorn – ASGI Server
- psycopg / psycopg2 – PostgreSQL 資料庫連線
- MediaPipe – 現成的動作與姿態偵測影像處理框架
- Nginx – Web Server 與系統入口
- WebSocket API – 即時資料同步
- systemd / systemd timer – Linux 系統服務與排程管理
- Git / GitHub – 版本控制與團隊協作
## Implementation Process
1. System Architecture Design
    - 規劃前端、後端與即時通訊模組
    - 設計 API 與資料庫結構

2. Linux Environment Setup
    - 在 Linux 虛擬機中建置系統環境
    - 安裝與設定 Nginx、Python 與 PostgreSQL

3. Backend Implementation
    - 使用 FastAPI 建立登入、寵物狀態與排行榜相關 API
    - 與 PostgreSQL 進行資料存取與狀態更新

4. Real-time Communication
    - 透過 WebSocket 實作即時狀態同步
    - 支援大廳狀態、排行榜與互動資料即時更新

5. Image Input and Motion Detection
    - 使用電腦內建攝影機作為影像輸入來源
    - 透過 MediaPipe 進行動作與姿態偵測
    - 系統僅使用 MediaPipe 提供的現成功能，未進行模型訓練
    - 將偵測結果轉換為使用者互動事件，傳送至後端系統處理

6. Scheduled System Tasks (systemd timer)
    - 透過 systemd timer 定期觸發後端服務
    - 用於定期更新寵物體力與狀態數值
    - systemd timer 與 systemd service 搭配，使背景任務可由系統層級管理

7. Frontend Integration
    - 前端透過 API 與 WebSocket 與後端系統溝通
    - 使用者可即時查看寵物狀態與排行榜變化

8. Deployment and Testing
    - 透過 Nginx 部署整體系統
    - 測試多使用者同時連線與即時互動功能
## Knowledge from Lecture
本專題實際應用了 Linux System Administration 課程中所學的知識，包括：
- Linux 系統環境建置與管理
- Web Server（Nginx）部署與設定
- Client / Server 架構概念
- 即時通訊（WebSocket）
- 應用程式層級的 timer 機制
- 背景服務與系統資源管理
- Git 版本控制與團隊協作
## Installation
1. Clone repository
```
git clone <repository-url>
```
2. Install Python dependencies
```
pip install -r requirements.txt
```
3. Setup PostgreSQL database
    - 建立資料表與初始資料
4. Start backend server
```
sudo systemctl enable pet-backend.service
sudo systemctl enable pet-backend.timer
sudo systemctl start pet-backend.timer
```
5. Configure and start Nginx
## Usage
1. 使用瀏覽器進入系統首頁
2. 使用者登入後即可查看虛擬寵物狀態 
3. 透過動作偵測或互動影響寵物體力與積分
4. systemd timer 會定期更新寵物狀態
5. 排行榜與狀態會即時更新顯示
## Job Assignment
| 學號 | 姓名 | 分工 |
| -------- | -------- | -------- |
| 112213025 | 施淯馨 | 前端介面設計與使用者互動功能  |
| 112213034 | 郭家言 | 後端開發、系統串接、Mediapipe  |
| 112213018 | 林秀萍 | WebSocket 即時通訊與同步功能 |
| 112213016 | 陳詩穎 | systemd timer、排程設定、ReadMe 撰寫  |
## References
- FastAPI Documentation
- Nginx Official Documentation
- PostgreSQL Documentation
- MediaPipe Documentation
- systemd.timer Documentation
- Linux System Administration Lecture Slides




