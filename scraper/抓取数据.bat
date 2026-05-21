@echo off
cd /d "E:\football-tactical-board\scraper"

echo ======================================
echo   Football Tactical Board - Scraper
echo ======================================
echo.
echo [1/2] Installing dependencies...
"C:\Program Files\Python311\python.exe" -m pip install -q -r "E:\football-tactical-board\scraper\requirements.txt"

echo [2/2] Scraping match data...
echo.
"C:\Program Files\Python311\python.exe" "E:\football-tactical-board\scraper\scraper.py" %*
echo.
echo ======================================
echo   DONE!
echo   Open tactical board, click Import JSON
echo   Select: match_data.json
echo ======================================
echo.
pause
