@echo off
cd /d "E:\football-tactical-board\scraper"

echo ======================================
echo   Auto Scraper - 60s interval
echo   Press Ctrl+C to stop
echo ======================================
echo.

"C:\Program Files\Python311\python.exe" -m pip install -q -r "E:\football-tactical-board\scraper\requirements.txt"

:loop
echo Scraping...
"C:\Program Files\Python311\python.exe" "E:\football-tactical-board\scraper\scraper.py" --source both
echo Done. Next refresh in 60s...
timeout /t 60 /nobreak >nul
goto loop
