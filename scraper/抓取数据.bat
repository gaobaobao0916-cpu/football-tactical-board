@echo off
chcp 65001 >nul
cd /d "E:\football-tactical-board\scraper"
echo.
echo ======================================
echo   足球战术板 - 数据抓取器
echo   球探体育 + 雷速体育 双源抓取
echo ======================================
echo.
echo [1/2] 检查依赖...

"C:\Program Files\Python311\python.exe" -m pip install -q -r "E:\football-tactical-board\scraper\requirements.txt"
if %errorlevel% neq 0 (
    echo ❌ 依赖安装失败，请检查网络连接
    pause
    exit /b 1
)

echo [2/2] 开始抓取数据...
echo.
"C:\Program Files\Python311\python.exe" "E:\football-tactical-board\scraper\scraper.py" %*
echo.
echo ======================================
echo   抓取完成！
echo   请打开战术板 → 点「导入JSON」
echo   选择 match_data.json
echo ======================================
echo.
pause
