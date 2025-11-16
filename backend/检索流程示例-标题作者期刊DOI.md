# 检索流程示例：标题 + 作者 + 期刊 + DOI

## 输入场景

**用户输入的关键词**:
```json
{
  "title": "The China Alzheimer Report 2022",
  "authors": ["Ren R", "Qi J", "Lin S"],
  "journal": "Gen Psychiatr",
  "doi": "10.1136/gpsych-2022-100751"
}
```

**特点**:
- ✅ 有标题
- ✅ 有作者（多个）
- ✅ 有期刊
- ✅ 有DOI
- ❌ 无年份
- ❌ 无PMID
- ❌ 无卷号、期号、页码

---

## 完整检索流程

### 步骤1: 检查优先级0（PMID直接搜索）

**执行代码**:
```python
if keywords.get("pmid"):
    # 执行PMID搜索
    ...
```

**结果**: 
- ❌ 输入中没有 `pmid` 字段
- ⏭️ **跳过**，继续下一步

**日志输出**:
```
[优先级0] 未检测到PMID，跳过
```

---

### 步骤2: 执行优先级1（DOI搜索）⭐ **关键步骤**

**执行代码**:
```python
if keywords.get("doi"):
    logger.info(f"[优先级1] 使用 DOI 检索: {keywords['doi']}")
    pmid = await self.search_by_doi(keywords["doi"])
    if pmid and pmid not in seen_pmids:
        article = await self.fetch_article_details(pmid)
        if article:
            return results  # 直接返回，跳过所有后续步骤
```

**详细流程**:

#### 2.1 DOI格式清理
```python
doi = "10.1136/gpsych-2022-100751"
# 清理格式（去除 https://doi.org/ 或 doi: 前缀）
doi = doi.strip().replace("https://doi.org/", "").replace("doi:", "").strip()
# 结果: "10.1136/gpsych-2022-100751"
```

#### 2.2 发送DOI搜索请求
```python
# 请求URL
GET https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi

# 请求参数
{
    "db": "pubmed",
    "term": "10.1136/gpsych-2022-100751[DOI]",
    "retmode": "json",
    "retmax": 1
}

# 预期响应
{
    "esearchresult": {
        "idlist": ["39700052"]  # 找到PMID
    }
}
```

**日志输出**:
```
[优先级1] 使用 DOI 检索: 10.1136/gpsych-2022-100751
  通过 DOI 搜索: 10.1136/gpsych-2022-100751
  发送请求: GET https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi
  请求参数: {'db': 'pubmed', 'term': '10.1136/gpsych-2022-100751[DOI]', ...}
  响应状态码: 200
  找到 PMID: 39700052
```

#### 2.3 获取文章详细信息
```python
# 使用找到的PMID获取文章详情
GET https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi

# 请求参数
{
    "db": "pubmed",
    "id": "39700052",
    "retmode": "xml"
}

# 返回的XML数据包含：
# - 标题: "The China Alzheimer Report 2022"
# - 作者: ["Ren R", "Qi J", "Lin S", ...]
# - 期刊: "General Psychiatry"
# - 年份: 2022
# - 卷号: 35
# - 期号: 1
# - 页码: e100751
# - DOI: 10.1136/gpsych-2022-100751
# - 摘要: ...
```

**日志输出**:
```
  获取文章详情: PMID=39700052
  发送请求: GET https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi
  响应状态码: 200
  解析成功: 标题=The China Alzheimer Report 2022...
  检索到文章: The China Alzheimer Report 2022...
```

#### 2.4 直接返回结果 ⚡ **关键点**

**执行代码**:
```python
if article:
    article["pmid"] = pmid
    results.append(article)
    seen_pmids.add(pmid)
    logger.info(f"PubMed 检索完成，共找到 {len(results)} 篇文章")
    return results  # ⚠️ 直接返回，不会执行后续的优先级2、3、4
```

**结果**: 
- ✅ 找到文章，**直接返回**
- ⏭️ **跳过**优先级2（精确匹配）
- ⏭️ **跳过**优先级3（模糊匹配）
- ⏭️ **跳过**优先级4（相似度排序）

**日志输出**:
```
PubMed 检索完成，共找到 1 篇文章
```

---

### 步骤3: 相似度计算（在API路由层）

**注意**: 虽然检索服务直接返回了结果，但在API路由层（`routes.py`）仍然会计算相似度。

**执行代码**（在 `routes.py` 中）:
```python
# 计算相似度
similarity = similarity_service.calculate_similarity(
    keywords_dict,  # 原始关键词
    article_keywords  # 从PubMed获取的文章关键词
)
```

**输入对比**:

| 字段 | 原始关键词 | PubMed文章 | 匹配情况 |
|------|-----------|-----------|---------|
| DOI | 10.1136/gpsych-2022-100751 | 10.1136/gpsych-2022-100751 | ✅ 完全匹配 |
| 标题 | The China Alzheimer Report 2022 | The China Alzheimer Report 2022 | ✅ 完全匹配 |
| 作者 | ["Ren R", "Qi J", "Lin S"] | ["Ren R", "Qi J", "Lin S", ...] | ✅ 前3个匹配 |
| 期刊 | Gen Psychiatr | General Psychiatry | ⚠️ 格式不同（缩写vs全名） |
| 年份 | 无 | 2022 | ❌ 原始缺失 |
| 卷号 | 无 | 35 | ❌ 原始缺失 |
| 期号 | 无 | 1 | ❌ 原始缺失 |

**相似度计算过程**:

```python
# 1. DOI完全匹配检查
if original["doi"] == matched["doi"]:
    return 1.0  # 100%匹配，直接返回
```

**结果**: 
- ✅ **DOI完全匹配** → **相似度 = 1.0（100%）**

**日志输出**:
```
开始计算相似度
原始关键词: {'title': '...', 'authors': [...], 'journal': '...', 'doi': '...'}
匹配文章关键词: {'title': '...', 'authors': [...], 'journal': '...', 'doi': '...'}
  [DOI] 完全匹配: 10.1136/gpsych-2022-100751 == 10.1136/gpsych-2022-100751, 相似度=100%
最终相似度: 1.0000
```

---

### 步骤4: 返回结果给前端

**返回数据格式**:
```json
{
    "reference_id": "ref_1",
    "matched_articles": [
        {
            "pmid": "39700052",
            "title": "The China Alzheimer Report 2022",
            "authors": ["Ren R", "Qi J", "Lin S", "Tang Y", "Dong Q", ...],
            "journal": "General Psychiatry",
            "year": 2022,
            "volume": "35",
            "issue": "1",
            "pages": "e100751",
            "doi": "10.1136/gpsych-2022-100751",
            "abstract": "...",
            "keywords": {
                "title": "The China Alzheimer Report 2022",
                "authors": ["Ren R", "Qi J", "Lin S", ...],
                "journal": "General Psychiatry",
                "year": 2022,
                "volume": "35",
                "issue": "1",
                "pages": "e100751",
                "doi": "10.1136/gpsych-2022-100751"
            },
            "similarity_score": 1.0,
            "differences": {}
        }
    ],
    "status": "matched"
}
```

**关键信息**:
- ✅ `similarity_score: 1.0` - 100%匹配
- ✅ `differences: {}` - 无差异（因为DOI完全匹配，直接返回100%）
- ✅ `status: "matched"` - 匹配成功

---

## 流程图

```
输入: {title, authors, journal, doi}
    ↓
[优先级0] 检查PMID
    ↓ (无PMID，跳过)
[优先级1] DOI搜索 ⭐
    ├─ 清理DOI格式
    ├─ 发送 esearch 请求: "10.1136/gpsych-2022-100751[DOI]"
    ├─ 获取PMID: 39700052
    ├─ 发送 efetch 请求获取文章详情
    └─ 找到文章 ✅
    ↓
直接返回结果 ⚡ (跳过优先级2、3、4)
    ↓
[API路由层] 计算相似度
    ├─ DOI完全匹配检查
    └─ 相似度 = 1.0 (100%)
    ↓
返回给前端
    └─ matched_articles: [1篇文章]
       similarity_score: 1.0
       status: "matched"
```

---

## 关键设计点

### 1. DOI优先策略 ⭐

**为什么DOI搜索后直接返回？**

- **唯一性**: DOI是数字对象唯一标识符，完全匹配意味着是同一篇文章
- **可靠性**: DOI匹配的可靠性是100%，无需进一步验证
- **效率**: 避免不必要的搜索步骤，提高响应速度

**代码逻辑**:
```python
if pmid and pmid not in seen_pmids:
    article = await self.fetch_article_details(pmid)
    if article:
        return results  # 直接返回，不执行后续步骤
```

### 2. 相似度计算的简化

**为什么DOI匹配时相似度直接返回1.0？**

- **唯一性保证**: DOI完全匹配 = 同一篇文章 = 100%相似度
- **性能优化**: 避免计算其他字段的相似度，节省计算资源
- **逻辑清晰**: 唯一标识符匹配时，其他字段的差异不影响结果

**代码逻辑**:
```python
# 在 similarity_service.py 中
if original.get("doi") and matched.get("doi"):
    if original["doi"].lower().strip() == matched["doi"].lower().strip():
        return 1.0  # 100%匹配，直接返回
```

### 3. 其他字段的作用

**虽然输入有标题、作者、期刊，但为什么没有使用？**

- **效率优先**: DOI搜索已经找到唯一匹配，无需使用其他字段
- **避免误判**: 如果使用标题+作者+期刊搜索，可能会因为格式差异导致找不到或找到多篇
- **数据补全**: 虽然检索时没用，但返回的文章信息会包含完整的标题、作者、期刊等信息，可以用于补全原始参考文献

---

## 特殊情况处理

### 情况1: DOI格式差异

**输入**: `doi: "https://doi.org/10.1136/gpsych-2022-100751"`

**处理**:
```python
doi = doi.strip().replace("https://doi.org/", "").replace("doi:", "").strip()
# 结果: "10.1136/gpsych-2022-100751"
```

**结果**: ✅ 自动清理格式，正常搜索

---

### 情况2: DOI未找到

**输入**: `doi: "10.1234/invalid-doi"`

**处理流程**:
```
[优先级1] DOI搜索
  → 发送请求
  → 响应: {"esearchresult": {"idlist": []}}  # 空列表
  → 未找到PMID
  → 继续执行优先级2
```

**后续流程**:
- 会使用标题+作者+期刊进行精确匹配
- 虽然缺少年份，但会尝试其他字段组合

---

### 情况3: DOI找到但文章详情获取失败

**处理流程**:
```
[优先级1] DOI搜索
  → 找到PMID: 39700052
  → 获取文章详情
  → 失败（网络错误、文章不存在等）
  → 继续执行优先级2
```

**后续流程**:
- 会使用标题+作者+期刊进行精确匹配
- 作为后备方案，确保能找到文章

---

## 性能分析

### 时间消耗

| 步骤 | 操作 | 预计时间 |
|------|------|---------|
| DOI格式清理 | 字符串处理 | < 1ms |
| DOI搜索请求 | HTTP请求 | 200-500ms |
| 文章详情获取 | HTTP请求 | 200-500ms |
| 相似度计算 | 本地计算 | < 1ms |
| **总计** | | **400-1000ms** |

### 对比：如果使用标题+作者+期刊搜索

| 步骤 | 操作 | 预计时间 |
|------|------|---------|
| 构建查询 | 字符串处理 | < 1ms |
| 标题+作者+期刊搜索 | HTTP请求 | 200-500ms |
| 可能找到多篇 | 需要筛选 | - |
| 获取每篇文章详情 | HTTP请求 × N | 200-500ms × N |
| 计算相似度 | 本地计算 × N | < 1ms × N |
| **总计** | | **400-1000ms × (1+N)** |

**优势**: DOI搜索通常只返回1篇，避免了多篇文章的获取和筛选，效率更高。

---

## 总结

### 核心流程

1. **优先级1（DOI搜索）** → 找到PMID → 获取文章详情 → **直接返回**
2. **跳过优先级2、3、4**（因为已经找到唯一匹配）
3. **相似度计算** → DOI完全匹配 → **相似度 = 1.0**
4. **返回结果** → 1篇文章，100%匹配

### 关键特点

- ✅ **最快**: 只需2次API调用（搜索+获取详情）
- ✅ **最可靠**: DOI是唯一标识符，100%准确
- ✅ **最简洁**: 无需复杂的多字段组合和相似度筛选
- ✅ **最完整**: 返回的文章信息包含所有字段（年份、卷号、期号等），可以补全原始参考文献

### 设计优势

这种设计充分利用了DOI作为唯一标识符的特性，在保证准确性的同时，最大化了检索效率，是检索策略中最优的路径。

