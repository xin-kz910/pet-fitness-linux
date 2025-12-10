#!/bin/bash

# 專案根目錄 (確保路徑正確)
PROJECT_ROOT="/home/jiayen/Desktop/pet_project/backend"
PYTHON_BIN="$PROJECT_ROOT/venv/bin/python"

# 1. 進入專案根目錄
cd $PROJECT_ROOT

# 2. **關鍵修正：** 導出 PYTHONPATH 環境變數
#    這會告訴 Python 在哪裡尋找模組
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# 3. 執行 Python 腳本 (使用完整的虛擬環境 Python)
#    注意：因為我們已經在上面設定了 PYTHONPATH，所以可以直接執行
$PYTHON_BIN cron/energy_decay.py
