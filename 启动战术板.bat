@echo off
cd /d "E:\football-tactical-board"

echo ============================================
echo   Football Tactical Board v1.0
echo ============================================
echo.
echo Starting local server...
echo.
start "" http://localhost:8766/index.html
"C:\Program Files\Python311\python.exe" -m http.server 8766
pause
