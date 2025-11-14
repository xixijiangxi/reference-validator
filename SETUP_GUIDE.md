# 设置指南

## 完整设置步骤

### 第一步：环境准备

1. **安装Python 3.9+**
   - 访问 https://www.python.org/downloads/
   - 下载并安装Python
   - 验证安装：`python --version`

2. **安装Node.js 18+**
   - 访问 https://nodejs.org/
   - 下载并安装Node.js
   - 验证安装：`node --version` 和 `npm --version`

### 第二步：获取API密钥

1. **DashScope API Key**
   - 访问 https://dashscope.console.aliyun.com/
   - 注册/登录账号
   - 创建API Key
   - 复制API Key备用

2. **PubMed邮箱**（可选但推荐）
   - 使用你的邮箱地址
   - 用于PubMed API调用，避免频率限制

### 第三步：安装依赖

1. **安装后端依赖**
```bash
cd backend
pip install -r requirements.txt
```

如果遇到权限问题，使用：
```bash
pip install --user -r requirements.txt
```

2. **安装前端依赖**
```bash
cd frontend
npm install
```

如果遇到网络问题，可以使用国内镜像：
```bash
npm install --registry=https://registry.npmmirror.com
```

### 第四步：配置环境变量

1. **创建.env文件**
```bash
# Windows
copy backend\.env.example backend\.env

# Linux/Mac
cp backend/.env.example backend/.env
```

2. **编辑.env文件**
打开 `backend/.env` 文件，填入你的信息：
```
DASHSCOPE_API_KEY=sk-your-actual-api-key-here
PUBMED_EMAIL=your_email@example.com
```

### 第五步：启动应用

**方式一：使用启动脚本（推荐）**

Windows:
```bash
start.bat
```

Linux/Mac:
```bash
chmod +x start.sh
./start.sh
```

**方式二：手动启动**

1. 启动后端（第一个终端）：
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

2. 启动前端（第二个终端）：
```bash
cd frontend
npm run dev
```

### 第六步：访问应用

打开浏览器访问：`http://localhost:5173`

## 常见问题

### Q1: 后端启动失败，提示模块未找到
**解决方案：**
```bash
cd backend
pip install -r requirements.txt
```

### Q2: 前端启动失败，提示端口被占用
**解决方案：**
- 修改 `frontend/vite.config.ts` 中的端口号
- 或关闭占用5173端口的其他程序

### Q3: API调用失败，提示401错误
**解决方案：**
- 检查 `backend/.env` 文件中的API Key是否正确
- 确认API Key是否有效且有足够的额度

### Q4: PubMed查询无结果
**解决方案：**
- 检查网络连接
- 确认输入的参考文献格式是否正确
- 尝试使用更完整的参考文献信息

### Q5: 大模型返回格式错误
**解决方案：**
- 检查API Key是否正确配置
- 确认DashScope账户有足够的额度
- 查看后端日志了解详细错误信息

## 测试建议

1. **使用示例数据**
   - 使用 `EXAMPLE_REFERENCES.txt` 中的示例数据进行测试
   - 验证基本功能是否正常

2. **逐步测试**
   - 先测试单条参考文献
   - 再测试多条参考文献
   - 最后测试不同格式的参考文献

3. **检查结果**
   - 验证参考文献是否正确拆分
   - 验证关键词是否正确提取
   - 验证PubMed查询是否返回结果
   - 验证相似度计算是否合理

## 下一步

- 根据实际需求调整Prompt
- 优化相似度计算权重
- 添加更多参考文献格式支持
- 优化UI界面和用户体验

