@echo off
chcp 65001 >nul
cd /d "E:\football-tactical-board\scraper"
echo.
echo ======================================
echo   定时抓取模式 (每60秒刷新)
echo   按 Ctrl+C 停止
echo ======================================
echo.

"C:\Program Files\Python311\python.exe" -m pip install -q -r "E:\football-tactical-board\scraper\requirements.txt"

:loop
echo [%date% %time%] 抓取中...
"C:\Program Files\Python311\python.exe" "E:\football-tactical-board\scraper\scraper.py" --source both
echo %time% 完成，60秒后刷新...
timeout /t 60 /nobreak >nul
goto loop
