# 部署指南 - 如何分享应用给他人体验

本文档提供多种方式，让其他人可以访问和使用你的参考文献校验工具。

## 方案一：内网穿透（推荐 - 最简单快速）⭐

### 使用 ngrok（免费，最简单）

1. **注册并下载 ngrok**
   - 访问 https://ngrok.com/
   - 注册账号（免费）
   - 下载 Windows 版本：https://ngrok.com/download
   - 解压到任意目录

2. **获取 authtoken**
   - 登录 ngrok 控制台
   - 在 "Getting Started" 页面找到你的 authtoken
   - 在命令行运行：`ngrok config add-authtoken YOUR_TOKEN`

3. **启动应用**
   ```bash
   # 先启动你的应用（使用 start.bat 或手动启动）
   start.bat
   ```

4. **启动 ngrok 隧道**
   ```bash
   # 新开一个命令行窗口，运行：
   ngrok http 5173
   ```
   
   这会显示类似以下的信息：
   ```
   Forwarding   https://xxxx-xxx-xxx-xxx.ngrok-free.app -> http://localhost:5173
   ```

5. **分享链接**
   - 将显示的 `https://xxxx-xxx-xxx-xxx.ngrok-free.app` 链接分享给其他人
   - 注意：免费版链接每次重启都会变化，付费版可以固定域名

### 使用 frp（免费，可自建服务器）

如果你有自己的服务器，可以使用 frp 进行内网穿透：

1. **服务器端配置**（在你的服务器上）
   ```ini
   # frps.ini
   [common]
   bind_port = 7000
   ```

2. **客户端配置**（在你的本地电脑上）
   ```ini
   # frpc.ini
   [common]
   server_addr = YOUR_SERVER_IP
   server_port = 7000

   [web]
   type = http
   local_port = 5173
   custom_domains = your-domain.com
   ```

3. **启动**
   ```bash
   # 服务器端
   ./frps -c frps.ini
   
   # 客户端
   ./frpc -c frpc.ini
   ```

### 使用 花生壳（国内，有免费版）

1. 访问 https://hsk.oray.com/
2. 注册账号并下载客户端
3. 添加映射：内网地址 `http://localhost:5173`
4. 获得外网访问地址

---

## 方案二：云服务器部署（推荐 - 最专业）⭐

### 使用 Railway（免费额度，简单）

1. **准备代码**
   - 确保代码已推送到 GitHub
   - 创建 `railway.json` 配置文件（见下方）

2. **部署步骤**
   - 访问 https://railway.app/
   - 使用 GitHub 账号登录
   - 点击 "New Project" -> "Deploy from GitHub repo"
   - 选择你的仓库
   - Railway 会自动检测并部署

3. **配置环境变量**
   - 在 Railway 项目设置中添加：
     - `DASHSCOPE_API_KEY=your_key`
     - `PUBMED_EMAIL=your_email`

### 使用 Render（免费，简单）

1. **创建 `render.yaml`**（见下方配置）

2. **部署步骤**
   - 访问 https://render.com/
   - 使用 GitHub 账号登录
   - 创建 "New Web Service"
   - 连接 GitHub 仓库
   - Render 会自动部署

### 使用 Vercel（前端）+ Railway/Render（后端）

1. **部署前端到 Vercel**
   ```bash
   cd frontend
   npm install -g vercel
   vercel
   ```

2. **部署后端到 Railway/Render**
   - 按照上述步骤部署后端

3. **修改前端 API 地址**
   - 在 `frontend/src/services/api.ts` 中修改后端地址

---

## 方案三：局域网访问（同一网络）

如果其他人跟你连接在同一个局域网（WiFi），可以直接访问：

1. **修改后端 CORS 配置**
   - 编辑 `backend/app/main.py`
   - 修改 `allow_origins` 为 `["*"]`（仅用于测试）

2. **获取本机 IP 地址**
   ```bash
   # Windows
   ipconfig
   # 找到 IPv4 地址，例如：192.168.1.100
   ```

3. **启动应用**
   ```bash
   start.bat
   ```

4. **分享地址**
   - 前端：`http://YOUR_IP:5173`
   - 例如：`http://192.168.1.100:5173`

---

## 方案四：Docker 容器化部署

### 创建 Docker 配置

1. **创建 `Dockerfile`**（见下方）

2. **创建 `docker-compose.yml`**（见下方）

3. **构建和运行**
   ```bash
   docker-compose up -d
   ```

4. **分享**
   - 将 Docker 镜像导出分享
   - 或推送到 Docker Hub

---

## 配置修改说明

### 1. 修改后端 CORS 配置（允许外部访问）

编辑 `backend/app/main.py`：

```python
# 修改前
allow_origins=["http://localhost:5173", "http://localhost:3000"],

# 修改后（允许所有来源，仅用于测试）
allow_origins=["*"],

# 或指定具体域名（推荐用于生产环境）
allow_origins=[
    "http://localhost:5173",
    "https://your-domain.com",
    "https://xxxx.ngrok-free.app"
],
```

### 2. 修改前端 API 地址（如果后端部署在不同地址）

编辑 `frontend/src/services/api.ts`：

```typescript
// 修改前
const API_BASE_URL = 'http://localhost:8000';

// 修改后（根据实际部署地址）
const API_BASE_URL = 'https://your-backend-domain.com';
```

### 3. 生产环境配置

**后端生产环境启动：**
```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**前端生产环境构建：**
```bash
cd frontend
npm run build
# 构建后的文件在 frontend/dist 目录
```

---

## 推荐方案对比

| 方案 | 难度 | 成本 | 适用场景 |
|------|------|------|----------|
| ngrok 内网穿透 | ⭐ 简单 | 免费/付费 | 快速分享，临时测试 |
| 云服务器部署 | ⭐⭐ 中等 | 免费/付费 | 长期使用，正式分享 |
| 局域网访问 | ⭐ 简单 | 免费 | 同一网络，内部测试 |
| Docker 容器化 | ⭐⭐⭐ 复杂 | 免费 | 技术用户，批量部署 |

---

## 快速开始（推荐：ngrok）

1. 下载 ngrok：https://ngrok.com/download
2. 注册并获取 token
3. 配置：`ngrok config add-authtoken YOUR_TOKEN`
4. 启动应用：`start.bat`
5. 启动隧道：`ngrok http 5173`
6. 分享链接给他人

**注意：** 免费版 ngrok 链接每次重启都会变化，适合临时分享。

---

## 安全提示

⚠️ **重要安全注意事项：**

1. **不要在生产环境使用 `allow_origins=["*"]`**
   - 仅用于测试和开发
   - 生产环境应指定具体域名

2. **保护 API Key**
   - 不要将 `.env` 文件提交到代码仓库
   - 使用环境变量或密钥管理服务

3. **使用 HTTPS**
   - ngrok 免费版提供 HTTPS
   - 生产环境建议使用 HTTPS

4. **限制访问**
   - 考虑添加身份验证
   - 限制 API 调用频率

---

## 常见问题

### Q: ngrok 链接访问时显示 "ngrok 404"？
A: 确保本地应用已启动，并且 ngrok 指向的端口正确（5173）。

### Q: 其他人无法访问？
A: 检查防火墙设置，确保端口 5173 和 8000 未被阻止。

### Q: 如何固定 ngrok 域名？
A: 需要升级到付费版，或使用 frp 自建服务器。

### Q: 部署后前端无法连接后端？
A: 检查 CORS 配置和前端 API 地址设置。

---

## 需要帮助？

如果遇到问题，请检查：
1. 本地应用是否正常运行
2. 网络连接是否正常
3. 防火墙设置
4. 端口是否被占用


