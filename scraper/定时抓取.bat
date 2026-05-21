@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo ================================================
echo   定时抓取模式 (每60秒刷新一次)
echo   按 Ctrl+C 停止
echo ================================================
echo.
echo 安装依赖...
pip install -q -r requirements.txt
echo.

:loop
echo [%date% %time%] 抓取中...
python scraper.py --format json
echo [%date% %time%] 完成，等待60秒...
echo.
timeout /t 60 /nobreak >nul
goto loop
