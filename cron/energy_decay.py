# cron/energy_decay.py

"""
每 20 分鐘執行一次：
- 所有寵物 energy -= 5（不能 < 0）
- 若這次「剛好變成 0」（原本 > 0，現在 = 0）→ score -= 1
- 更新 status = SLEEPING / TIRED / ACTIVE

請放在 backend 專案的 cron/ 資料夾底下：
backend/
  app/
    main.py
  cron/
    energy_decay.py
"""
# ==========================================================
# 🚨 緊急修正：強制設定專案根目錄 (必須放在最頂端) 🚨
# ==========================================================
import sys
import os

# 1. 取得腳本的當前目錄 (backend/cron/)
current_dir = os.path.dirname(os.path.abspath(__file__))
# 2. 設定專案根目錄 (backend/)
project_root = os.path.join(current_dir, '..')

# 3. 將專案根目錄加入 Python 搜尋路徑
if project_root not in sys.path:
    sys.path.insert(0, project_root) # 使用 insert(0) 確保優先級

# ==========================================================


"""
每 20 分鐘執行一次：
- 所有寵物 energy -= 5（不能 < 0）
... (略) ...
"""

# 現在，Python 就能找到 app.main 模組了！
from app.main import SessionLocal, Pet, energy_to_status

def run_energy_decay():
    db = SessionLocal()
    try:
        pets = db.query(Pet).all()
        print(f"[CRON] 找到 {len(pets)} 隻寵物，開始更新體力 ...")

        for pet in pets:
            old_energy = pet.energy
            new_energy = max(0, old_energy - 5)

            if new_energy != old_energy:
                pet.energy = new_energy
                pet.status = energy_to_status(new_energy)

                # 🔻 從 >0 掉到 0 → score -1
                if old_energy > 0 and new_energy == 0:
                    pet.score -= 1
                    print(
                        f"[CRON] pet_id={pet.pet_id} {old_energy}->{new_energy}, score-1 => {pet.score}"
                    )
                else:
                    print(
                        f"[CRON] pet_id={pet.pet_id} {old_energy}->{new_energy}, score={pet.score}"
                    )

        db.commit()
        print("[CRON] 體力更新完成，已寫入資料庫。")

    except Exception as exc:
        db.rollback()
        print("[CRON][ERROR] 體力更新失敗：", exc)
    finally:
        db.close()


if __name__ == "__main__":
    run_energy_decay()

