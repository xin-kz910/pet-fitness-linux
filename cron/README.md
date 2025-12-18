# Background Jobs

此資料夾存放本專案的背景排程任務程式，  
主要負責「體力自然下降」與「排行榜更新」。

本專案原本規劃使用 `cron` 進行後端定時任務（如體力衰減、狀態更新等），
相關腳本與設定檔仍保留於 `cron/` 資料夾中作為設計紀錄。
後續改採 **systemd timer** 作為正式排程機制。
目前實際運作之排程任務皆由 `systemd timer` 管理，
`cron/` 資料夾部分內容僅保留作為開發歷程與替代方案參考，未於正式環境中啟用。

## 任務說明

- energy_decay.py  
  定期扣除寵物體力，當體力歸零時扣除排行榜分數。

- update_leaderboard.py  
  定期重新計算排行榜並寫入資料庫。

## 排程方式說明

- 專案早期於 VM 環境中曾使用 cron（crontab.txt）與 systemd timer 執行這些任務。
- 在最終 Docker 化版本中，因 container 不支援 systemd，
  改採 Application-level timer 於後端服務中觸發。
- crontab.txt 保留作為實作歷程與替代方案紀錄。

# systemd 操作
## 重新載入 systemd
```
sudo systemctl daemon-reload
```
## 啟用並啟動 timer
```
sudo systemctl enable pet-energy.timer
sudo systemctl start pet-energy.timer
```
## 確認 timer 是否真的在跑
```
systemctl list-timers
```
