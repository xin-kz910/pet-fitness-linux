#!/bin/bash

# 專案根目錄
PROJECT_ROOT="/home/jiayen/Desktop/pet_project/backend"

# 1. 進入專案根目錄 (確保所有相對路徑能找到)
cd $PROJECT_ROOT

# 2. 啟動虛擬環境 (載入其 bin 和環境變數)
source venv/bin/activate

# 3. 執行 Python 腳本
/home/jiayen/Desktop/pet_project/backend/venv/bin/python cron/energy_decay.py

# 4. 退出虛擬環境 (非必要，但良好習慣)
deactivate
