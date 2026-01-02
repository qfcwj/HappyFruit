@echo off
cd /d "%~dp0"

if not exist ".venv" (
    echo [ERROR] 还没安装环境！请先运行 install.bat
    pause
    exit /b
)

echo [INFO] HappyFruit 后台服务启动中...
echo [INFO] 请按 Alt+Q 呼出窗口
echo [INFO] 即使没有窗口出现，程序也在后台运行中

:: 直接启动 gui_app.py
start "" ".venv\Scripts\pythonw.exe" src\gui_app.py

exit