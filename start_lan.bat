@echo off
echo ========================================
echo 启动应用（局域网访问模式）
echo ========================================
echo.

REM 获取本机 IP 地址
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    set IP=%%a
    goto :found
)
:found
set IP=%IP:~1%

echo [1/3] 启动后端服务（允许外部访问）...
start "Backend Server" cmd /k "cd backend && set ALLOWED_ORIGINS=* && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

timeout /t 3 /nobreak >nul

echo [2/3] 启动前端服务（允许外部访问）...
start "Frontend Server" cmd /k "cd frontend && npm run dev -- --host"

timeout /t 3 /nobreak >nul

echo [3/3] 完成！
echo.
echo ========================================
echo 服务已启动：
echo - 后端: http://localhost:8000
echo - 前端: http://localhost:5173
echo.
echo 局域网访问地址：
echo - 前端: http://%IP%:5173
echo - 后端: http://%IP%:8000
echo ========================================
echo.
echo 提示：
echo 1. 确保其他设备连接在同一 WiFi/局域网
echo 2. 确保防火墙允许端口 5173 和 8000
echo 3. 在其他设备浏览器访问: http://%IP%:5173
echo.
echo 按任意键退出...
pause >nul


