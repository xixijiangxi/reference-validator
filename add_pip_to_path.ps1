# 添加pip到PATH环境变量
$scriptsPath = "C:\Users\renzhaoxi\AppData\Local\Python\pythoncore-3.14-64\Scripts"

# 获取当前用户PATH
$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")

# 检查是否已存在
if ($currentPath -notlike "*$scriptsPath*") {
    # 添加到PATH
    $newPath = if ($currentPath) { 
        "$currentPath;$scriptsPath" 
    } else { 
        $scriptsPath 
    }
    
    # 保存到环境变量
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    
    Write-Host "✓ 已成功将pip添加到PATH: $scriptsPath" -ForegroundColor Green
    Write-Host ""
    Write-Host "注意：需要重新打开PowerShell窗口才能使用pip命令" -ForegroundColor Yellow
} else {
    Write-Host "✓ PATH中已包含该路径" -ForegroundColor Green
}

# 刷新当前会话的PATH
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# 测试pip命令
Write-Host ""
Write-Host "测试pip命令..." -ForegroundColor Cyan
try {
    pip --version
    Write-Host "✓ pip命令可用！" -ForegroundColor Green
} catch {
    Write-Host "⚠ 当前会话中pip仍不可用，请重新打开PowerShell窗口" -ForegroundColor Yellow
}

