@echo off
REM 墨卷 · 展厅开机脚本（Windows）。放进「启动」文件夹或任务计划程序。
cd /d %~dp0\..\..
start "ink-relay" /min python server.py 8888
timeout /t 2 >nul
:loop
start /wait "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --kiosk --incognito --noerrdialogs --disable-session-crashed-bubble --autoplay-policy=no-user-gesture-required --app="http://127.0.0.1:8888/?preset=kiosk&grid=0"
echo browser exited, restarting in 3s
timeout /t 3 >nul
goto loop
