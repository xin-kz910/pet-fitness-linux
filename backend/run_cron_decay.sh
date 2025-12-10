#!/bin/bash

# 這是 Python 虛擬環境的解釋器路徑
PYTHON_BIN="/home/jiayen/Desktop/pet_project/backend/venv/bin/python"

# 直接使用絕對路徑執行 Python 腳本
# 所有的環境載入和路徑調整，都交由 Python 腳本自己處理
$PYTHON_BIN /home/jiayen/Desktop/pet_project/backend/cron/energy_decay.py
