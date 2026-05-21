@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo ======================================
echo   足球战术板 - 数据抓取器
echo   球探体育 + 雷速体育 双源抓取
echo ======================================
echo.
echo 正在安装依赖...
pip install -q -r requirements.txt
echo.
echo 开始抓取数据...
echo.
python scraper.py %*
echo.
echo 按任意键关闭...
pause >nul
