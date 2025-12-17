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
