# Windows PowerShell 使用 pip 的说明

## 问题说明

在Windows PowerShell中，如果直接使用 `pip` 命令可能会提示"无法识别"的错误。这是因为pip的安装路径没有添加到系统的PATH环境变量中。

## 解决方案

### 方法1：使用 `python -m pip`（推荐）

**这是最简单可靠的方法**，直接使用Python模块方式调用pip：

```powershell
# 安装包
python -m pip install package_name

# 安装requirements.txt中的所有依赖
python -m pip install -r requirements.txt

# 升级pip
python -m pip install --upgrade pip

# 查看已安装的包
python -m pip list
```

### 方法2：将pip添加到PATH（可选）

如果你想直接使用 `pip` 命令，可以将Python的Scripts目录添加到PATH：

1. **找到Python Scripts目录**
   ```powershell
   python -m pip --version
   # 输出会显示pip的位置，例如：
   # pip 25.3 from C:\Users\renzhaoxi\AppData\Local\Python\pythoncore-3.14-64\Lib\site-packages\pip
   # Scripts目录通常是：C:\Users\renzhaoxi\AppData\Local\Python\pythoncore-3.14-64\Scripts
   ```

2. **添加到PATH环境变量**
   - 右键"此电脑" → "属性" → "高级系统设置"
   - 点击"环境变量"
   - 在"用户变量"中找到"Path"，点击"编辑"
   - 点击"新建"，添加Scripts目录路径
   - 确定保存

3. **重启PowerShell**
   - 关闭当前PowerShell窗口
   - 重新打开PowerShell
   - 现在可以直接使用 `pip` 命令了

## 本项目推荐使用方法

**本项目推荐使用 `python -m pip`**，因为：
- ✅ 不需要修改系统环境变量
- ✅ 适用于所有Python安装方式
- ✅ 更可靠，不会因为PATH问题出错

## 安装本项目依赖

```powershell
# 进入backend目录
cd backend

# 安装所有依赖
python -m pip install -r requirements.txt

# 或者逐个安装（如果requirements.txt有问题）
python -m pip install fastapi uvicorn[standard] pydantic python-dotenv httpx dashscope beautifulsoup4 lxml python-multipart
```

## 验证安装

```powershell
# 检查Python版本
python --version

# 检查pip版本
python -m pip --version

# 查看已安装的包
python -m pip list
```

## 常见问题

### Q: 为什么使用 `python -m pip` 而不是 `pip`？
A: `python -m pip` 是Python官方推荐的方式，它确保使用当前Python环境中的pip，避免PATH配置问题。

### Q: 安装时提示权限错误？
A: 使用 `--user` 参数安装到用户目录：
```powershell
python -m pip install --user package_name
```

### Q: 安装速度慢？
A: 可以使用国内镜像源：
```powershell
python -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

