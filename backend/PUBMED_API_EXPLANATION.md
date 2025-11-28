# PubMed API 调用说明

## 1. 使用的接口

本项目使用的是 **NCBI E-Utilities API**，这是PubMed官方提供的免费API接口。

### API端点

1. **esearch.fcgi** - 用于搜索文献，返回PMID列表
   - URL: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi`
   - 功能：根据查询条件搜索文献，返回匹配的PMID（PubMed ID）列表

2. **efetch.fcgi** - 用于获取文献详细信息
   - URL: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi`
   - 功能：根据PMID获取文献的完整详细信息（标题、作者、期刊、摘要等）

## 2. 调用方式

### 搜索流程

```python
# 第一步：搜索文献（获取PMID）
GET https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi
参数：
  - db=pubmed          # 数据库：pubmed
  - term=查询条件       # 例如："title"[Title] AND "author"[Author]
  - retmode=json       # 返回格式：JSON
  - retmax=20          # 最多返回20条结果
  - email=your_email   # 你的邮箱（必需）

# 第二步：获取文献详情（根据PMID）
GET https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi
参数：
  - db=pubmed          # 数据库：pubmed
  - id=PMID            # 第一步返回的PMID
  - retmode=xml        # 返回格式：XML（包含完整信息）
  - email=your_email   # 你的邮箱（必需）
```

### 实际代码示例

```python
# 1. 通过DOI搜索
search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
params = {
    "db": "pubmed",
    "term": "10.1038/s41591-023-01234-5[DOI]",  # DOI查询
    "retmode": "json",
    "retmax": 1,
    "email": "your_email@example.com"
}
# 返回：{"esearchresult": {"idlist": ["12345678"]}}

# 2. 通过标题搜索
params = {
    "db": "pubmed",
    "term": '"Machine Learning in Medical Research"[Title]',
    "retmode": "json",
    "retmax": 20,
    "email": "your_email@example.com"
}

# 3. 组合查询（标题+作者+期刊+年份）
params = {
    "db": "pubmed",
    "term": '"Machine Learning"[Title] AND "Smith"[Author] AND "Nature Medicine"[Journal] AND 2023[Publication Date]',
    "retmode": "json",
    "retmax": 20,
    "email": "your_email@example.com"
}

# 4. 获取文献详情
fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
params = {
    "db": "pubmed",
    "id": "12345678",  # 从esearch获取的PMID
    "retmode": "xml",  # XML格式包含完整信息
    "email": "your_email@example.com"
}
# 返回：XML格式的完整文献信息
```

## 3. 为什么需要邮箱（Email）？

### 主要原因

1. **提高请求速率限制**
   - **不提供邮箱**：每秒最多3次请求
   - **提供邮箱**：每秒最多10次请求
   - 这对于批量处理参考文献非常重要！

2. **NCBI联系用户**
   - 如果API使用出现问题，NCBI可以通过邮箱联系你
   - 用于API使用情况的统计和监控

3. **API使用规范**
   - NCBI要求提供邮箱作为身份标识
   - 这是E-Utilities API的使用规范

### 重要提示

- **邮箱是必需的参数**，但不用于身份验证
- 可以使用任何有效的邮箱地址
- 建议使用真实邮箱，以便接收NCBI的重要通知
- 不会收到垃圾邮件，只是用于API使用情况通知

## 4. 查询策略（本项目实现）

### 优先级顺序

1. **DOI优先**（最高优先级）
   ```
   如果存在DOI → 直接使用DOI查询 → 如果找到，直接返回（100%匹配）
   ```

2. **标题检索**
   ```
   使用标题查询 → 如果结果唯一，返回该文献
   ```

3. **标题 + 第一作者**
   ```
   如果标题结果不唯一 → 添加第一作者进行组合查询
   ```

4. **标题 + 期刊 + 出版年**
   ```
   进一步缩小范围 → 提高检索精度
   ```

### 查询字段说明

- `[DOI]` - DOI号查询
- `[Title]` - 标题查询
- `[Author]` - 作者查询
- `[Journal]` - 期刊查询
- `[Publication Date]` - 出版日期查询

## 5. 返回数据格式

### esearch返回（JSON）

```json
{
  "esearchresult": {
    "count": "5",
    "retmax": "20",
    "retstart": "0",
    "idlist": ["12345678", "23456789", "34567890"]
  }
}
```

### efetch返回（XML）

```xml
<PubmedArticle>
  <MedlineCitation>
    <PMID>12345678</PMID>
    <Article>
      <ArticleTitle>Machine Learning in Medical Research</ArticleTitle>
      <AuthorList>
        <Author>
          <LastName>Smith</LastName>
          <ForeName>John</ForeName>
        </Author>
      </AuthorList>
      <Journal>
        <Title>Nature Medicine</Title>
      </Journal>
      <PubDate>
        <Year>2023</Year>
      </PubDate>
      <Volume>29</Volume>
      <Issue>5</Issue>
      <Pagination>
        <StartPage>1234</StartPage>
        <EndPage>1240</EndPage>
      </Pagination>
    </Article>
    <ArticleIdList>
      <ArticleId IdType="doi">10.1038/s41591-023-01234-5</ArticleId>
    </ArticleIdList>
  </MedlineCitation>
</PubmedArticle>
```

## 6. 参考文档

- **NCBI E-Utilities官方文档**: https://www.ncbi.nlm.nih.gov/books/NBK25497/
- **PubMed API文档**: https://pmc.ncbi.nlm.nih.gov/tools/developers/
- **E-Utilities使用指南**: https://www.ncbi.nlm.nih.gov/books/NBK25501/

## 7. 注意事项

1. **请求频率限制**
   - 提供邮箱：每秒最多10次请求
   - 建议在代码中添加适当的延迟，避免超过限制

2. **错误处理**
   - API可能返回错误，需要做好异常处理
   - 网络问题可能导致请求失败，需要重试机制

3. **数据解析**
   - XML格式需要正确解析
   - 某些字段可能为空，需要处理缺失数据的情况

4. **免费使用**
   - E-Utilities API完全免费
   - 不需要API Key（但提供邮箱可以提高速率限制）
   - 可以注册NCBI账号获取API Key以进一步提高限制


