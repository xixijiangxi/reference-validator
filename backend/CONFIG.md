# 环境配置文件说明

## 创建.env文件

请按照以下步骤创建环境配置文件：

### Windows用户：

1. 在 `backend` 目录下创建 `.env` 文件
2. 复制以下内容到文件中：

```
DASHSCOPE_API_KEY=your_dashscope_api_key_here
PUBMED_EMAIL=your_email@example.com
```

3. 将 `your_dashscope_api_key_here` 替换为你的实际 DashScope API Key
4. 将 `your_email@example.com` 替换为你的邮箱地址

### Linux/Mac用户：

```bash
cd backend
cp env_template.txt .env
# 然后编辑 .env 文件，填入你的实际配置
```

或者直接创建：

```bash
cd backend
cat > .env << EOF
DASHSCOPE_API_KEY=your_dashscope_api_key_here
PUBMED_EMAIL=your_email@example.com
EOF
```

## 获取 DashScope API Key

1. 访问 https://dashscope.console.aliyun.com/
2. 注册/登录账号
3. 在控制台创建API Key
4. 复制API Key到 `.env` 文件中

## 注意事项

- `.env` 文件包含敏感信息，已被添加到 `.gitignore`，不会被提交到版本控制
- 确保 `.env` 文件在 `backend` 目录下
- API Key格式通常以 `sk-` 开头

