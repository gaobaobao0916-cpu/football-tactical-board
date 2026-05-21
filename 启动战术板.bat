@echo off
chcp 65001 >nul
echo ============================================
echo   实时足球战术板 - 个人驾驶舱 v1.0
echo ============================================
echo.
echo 正在启动本地服务...
echo.
start "" http://localhost:8765/index.html
cd /d E:\football-tactical-board
python -m http.server 8765
pause
