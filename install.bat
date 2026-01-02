@echo off
echo [INFO] 正在初始化 HappyFruit...

:: 1. 创建标准的 Python 虚拟环境 (不依赖 Conda，更轻量)
:: 如果你电脑里有 python 命令，它会基于那个版本创建副本
python -m venv .venv

:: 2. 激活环境并安装依赖
echo [INFO] 正在安装依赖...
call .venv\Scripts\activate
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

echo.
echo [SUCCESS] 安装完成！
pause