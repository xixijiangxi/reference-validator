# 医学科研参考文献校验工具

一个用于校验、补全和纠正医学科研参考文献的Web应用工具。

## 功能特性

- 📝 支持多种参考文献格式识别（通用顺序编码制、通用著者出版年制、国标2015、APA、MLA、AMA、NLM）
- 🔍 自动拆分参考文献列表并提取关键词
- 🔎 基于PubMed API的智能文献检索
- 📊 相似度计算和差异高亮显示
- ✏️ 支持补全、替换、删除操作
- 📋 支持多种格式导出和复制

## 技术架构

### 前端
- **框架**: React 18 + TypeScript
- **构建工具**: Vite
- **样式**: Tailwind CSS
- **HTTP客户端**: Axios

### 后端
- **框架**: FastAPI
- **语言**: Python 3.9+
- **大模型API**: DashScope Qwen3
- **PubMed API**: NCBI E-Utilities

## 项目结构

```
reference-validator/
├── frontend/          # React前端应用
│   ├── src/
│   │   ├── components/    # React组件
│   │   ├── services/     # API服务
│   │   ├── types/        # TypeScript类型定义
│   │   ├── App.tsx       # 主应用组件
│   │   └── main.tsx      # 入口文件
│   ├── package.json
│   └── vite.config.ts
├── backend/          # FastAPI后端服务
│   ├── app/
│   │   ├── main.py       # FastAPI应用入口
│   │   ├── models.py     # 数据模型
│   │   ├── services/     # 业务逻辑服务
│   │   └── api/          # API路由
│   ├── requirements.txt
│   └── .env.example
├── README.md
└── .gitignore
```

## 快速开始

### 环境要求

- Node.js 18+
- Python 3.9+
- DashScope API Key（用于Qwen3）

### 安装步骤

1. **安装后端依赖**
```bash
cd backend
python -m pip install -r requirements.txt
```

> **Windows用户注意**：如果直接使用 `pip` 命令提示"无法识别"，请使用 `python -m pip` 代替。详见 `WINDOWS_PIP_GUIDE.md`

2. **配置环境变量**

`.env` 文件已经创建在 `backend` 目录下，请编辑该文件，填入你的实际配置：

**编辑 `backend/.env` 文件：**
```
DASHSCOPE_API_KEY=your_dashscope_api_key_here  # 替换为你的实际API Key
PUBMED_EMAIL=your_email@example.com            # 替换为你的邮箱
```

**获取 DashScope API Key：**
- 访问 https://dashscope.console.aliyun.com/
- 注册/登录账号
- 在控制台创建API Key
- 复制API Key到 `.env` 文件中

> 注意：`.env` 文件包含敏感信息，已被添加到 `.gitignore`，不会被提交到版本控制

3. **安装前端依赖**
```bash
cd frontend
npm install
```

4. **启动应用**

**Windows用户：**
```bash
start.bat
```

**Linux/Mac用户：**
```bash
chmod +x start.sh
./start.sh
```

**或者手动启动：**

启动后端服务：
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

启动前端开发服务器（新终端）：
```bash
cd frontend
npm run dev
```

5. **访问应用**
打开浏览器访问 `http://localhost:5173`

## 使用说明

1. **输入参考文献**：在左侧输入区粘贴或输入参考文献列表
2. **提交处理**：点击"提交"按钮，系统会自动拆分和识别每条参考文献
3. **查看结果**：右侧数据展示区会显示每条原始参考文献及其匹配结果
4. **处理操作**：
   - **补全**：点击"补全"按钮自动填充缺失信息
   - **替换**：从相似文献列表中选择一篇进行替换
   - **删除**：删除不需要的参考文献
5. **导出结果**：在最终结果区可以复制或导出为不同格式

## 核心功能说明

### 1. 参考文献拆分策略
- 使用DashScope Qwen3大模型识别参考文献边界
- 支持识别多种格式：顺序编码制、著者出版年制、国标2015、APA、MLA、AMA、NLM
- 自动识别每条参考文献的格式类型

### 2. 关键词提取策略
- 从每条参考文献中提取：标题、作者、期刊、年份、卷、期、页码、PubMedID、DOI
- 使用大模型进行智能提取，能提取多少提取多少

### 3. PubMed查询策略
按以下优先级顺序进行检索：
1. **DOI优先**：如果存在DOI，优先使用DOI检索
2. **标题检索**：使用标题进行检索
3. **标题+第一作者**：如果结果不唯一，添加第一作者进行组合检索
4. **标题+期刊+出版年**：进一步缩小范围

### 4. 相似度计算
- 关键词权重：DOI(30%) > PMID(25%) > 标题(20%) > 作者(15%) > 期刊(5%) > 年份(3%) > 卷期(2%)
- 100%匹配：如果DOI完全匹配，直接返回该文献
- 相似度阈值：只返回相似度≥50%的文献
- 差异标注：标红显示与原始参考文献不一致的关键词

## API文档

启动后端服务后，访问 `http://localhost:8000/docs` 查看Swagger API文档。

## 注意事项

1. **API密钥**：需要配置DashScope API Key才能使用大模型功能
2. **PubMed API**：建议配置有效的邮箱地址，避免API限制
3. **网络连接**：需要稳定的网络连接访问PubMed API
4. **处理时间**：大量参考文献处理可能需要较长时间，请耐心等待

## 部署和分享

想要将应用分享给其他人体验？请查看 [部署指南](DEPLOYMENT_GUIDE.md)

**快速方式（推荐）：**
1. 使用 ngrok 内网穿透（最简单）
2. 运行 `start_with_ngrok.bat` 脚本
3. 分享 ngrok 生成的公网地址

**其他方式：**
- 局域网访问：运行 `start_lan.bat`（同一 WiFi）
- 云服务器部署：Railway、Render 等
- Docker 容器化：使用 `docker-compose.yml`

详见 [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

## 许可证

MIT License
