@echo off
echo ========================================
echo 启动应用并配置 ngrok 内网穿透
echo ========================================
echo.

REM 检查 ngrok 是否安装
where ngrok >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [错误] 未找到 ngrok，请先安装：
    echo 1. 访问 https://ngrok.com/download
    echo 2. 下载并解压 ngrok.exe
    echo 3. 将 ngrok.exe 添加到系统 PATH 或放在当前目录
    echo.
    pause
    exit /b 1
)

echo [1/4] 启动后端服务（允许外部访问）...
start "Backend Server" cmd /k "cd backend && set ALLOWED_ORIGINS=* && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

timeout /t 3 /nobreak >nul

echo [2/4] 启动前端服务...
start "Frontend Server" cmd /k "cd frontend && npm run dev -- --host"

timeout /t 5 /nobreak >nul

echo [3/4] 启动 ngrok 隧道...
echo 注意：ngrok 会显示一个公网访问地址，请复制该地址分享给他人
echo.
start "ngrok Tunnel" cmd /k "ngrok http 5173"

timeout /t 2 /nobreak >nul

echo [4/4] 完成！
echo.
echo ========================================
echo 服务已启动：
echo - 后端: http://localhost:8000
echo - 前端: http://localhost:5173
echo - ngrok: 查看新打开的窗口获取公网地址
echo ========================================
echo.
echo 提示：
echo 1. ngrok 窗口会显示类似 "Forwarding https://xxx.ngrok-free.app" 的地址
echo 2. 将该地址分享给他人即可访问
echo 3. 免费版链接每次重启都会变化
echo.
echo 按任意键退出...
pause >nul


