@echo off
chcp 65001 >nul
echo ============================================
echo   足球战术板 · 在线部署工具
echo   当网络恢复时运行此脚本一键上线
echo ============================================
echo.
echo [1] 尝试 GitHub Pages 部署...
echo.
cd /d E:\football-tactical-board

:: 检查Git
git rev-parse --is-inside-work-tree >nul 2>&1
if %errorlevel% neq 0 (
    echo [FAIL] 未找到Git仓库，正在初始化...
    git init
    git checkout -b main
    git config user.email "gaobaobao0916@users.noreply.github.com"
    git config user.name "gaobaobao0916-cpu"
    git add -A
    git commit -m "deploy: football tactical board"
)

:: 尝试推送到GitHub
gh auth status >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] GitHub已认证，正在创建仓库...
    gh repo create gaobaobao0916-cpu/football-tactical-board --public --source=. --remote=origin --push 2>nul
    if %errorlevel% equ 0 (
        echo [OK] GitHub Pages 部署成功!
        echo [URL] https://gaobaobao0916-cpu.github.io/football-tactical-board/
        echo [注] 首次部署需要2-5分钟生效
        goto :done
    )
)

echo [FAIL] GitHub部署失败（网络不通或认证问题）
echo.
echo [2] 手动部署指引:
echo   - 在浏览器打开 https://github.com/gaobaobao0916-cpu
echo   - 新建仓库 football-tactical-board
echo   - 本地运行: git push origin main
echo   - 在仓库 Settings ^> Pages 中启用 GitHub Pages
echo.
echo [3] EdgeOne Pages 备选:
echo   - 登录 EdgeOne Pages 控制台
echo   - 上传 E:\football-tactical-board\index.html
echo.

:done
echo ============================================
echo   本地版已运行: http://localhost:8765
echo   双击"启动战术板.bat"即可使用
echo ============================================
pause
