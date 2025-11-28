"""详细测试检索查询字符串"""
import asyncio
import httpx
import json

async def test_queries():
    """测试各种查询字符串"""
    PUBMED_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    
    title = "A focus shift from sarcopenia to muscle health in the Asian Working Group for Sarcopenia 2025 Consensus Update"
    title_clean = title.rstrip('.')
    first_author = "Chen, L. K."
    processed_author = first_author.split(",")[0].strip() if "," in first_author else first_author.strip()
    journal = "Nature Aging"
    year = 2025
    
    queries = [
        # 测试1: 标题精确匹配
        {
            "name": "标题精确匹配",
            "term": f'"{title_clean}"[Title]',
        },
        # 测试2: 标题模糊匹配（所有词）
        {
            "name": "标题模糊匹配（所有词）",
            "term": f'({" AND ".join(title_clean.split())})[Title]',
        },
        # 测试3: 标题+作者（精确）
        {
            "name": "标题+作者（精确）",
            "term": f'"{title_clean}"[Title] AND "{processed_author}"[Author]',
        },
        # 测试4: 标题+作者（模糊）
        {
            "name": "标题+作者（模糊）",
            "term": f'({" AND ".join(title_clean.split())})[Title] AND {processed_author}[Author]',
        },
        # 测试5: 标题+期刊+年份（精确）
        {
            "name": "标题+期刊+年份（精确）",
            "term": f'"{title_clean}"[Title] AND "{journal}"[Journal] AND {year}[Publication Date]',
        },
        # 测试6: 标题+期刊+年份（模糊）
        {
            "name": "标题+期刊+年份（模糊）",
            "term": f'({" AND ".join(title_clean.split())})[Title] AND ({" AND ".join(journal.split())})[Journal] AND {year}[Publication Date]',
        },
        # 测试7: 关键词（去除停用词）
        {
            "name": "关键词（去除停用词）",
            "term": f'({" AND ".join([w for w in title_clean.split() if w.lower() not in {"the", "a", "an", "and", "or", "for", "of", "in", "on", "at", "to", "by", "with", "is", "are", "was", "were"} and len(w) > 2][:10])})[Title]',
        },
        # 测试8: 只搜索标题的前几个关键词
        {
            "name": "标题前10个词",
            "term": f'({" AND ".join(title_clean.split()[:10])})[Title]',
        },
        # 测试9: 只搜索标题的前15个词
        {
            "name": "标题前15个词",
            "term": f'({" AND ".join(title_clean.split()[:15])})[Title]',
        },
        # 测试10: 作者+期刊+年份
        {
            "name": "作者+期刊+年份",
            "term": f'{processed_author}[Author] AND "{journal}"[Journal] AND {year}[Publication Date]',
        },
        # 测试11: 只搜索标题中的核心词
        {
            "name": "核心关键词（sarcopenia muscle health）",
            "term": f'(sarcopenia AND muscle AND health)[Title]',
        },
    ]
    
    async with httpx.AsyncClient() as client:
        for query_info in queries:
            print(f"\n【{query_info['name']}】")
            print(f"  查询: {query_info['term'][:100]}...")
            
            try:
                search_url = f"{PUBMED_BASE_URL}/esearch.fcgi"
                params = {
                    "db": "pubmed",
                    "term": query_info['term'],
                    "retmode": "json",
                    "retmax": 20,
                    "sort": "relevance",
                }
                
                response = await client.get(search_url, params=params, timeout=10.0)
                
                if response.status_code == 200:
                    data = response.json()
                    id_list = data.get("esearchresult", {}).get("idlist", [])
                    count = data.get("esearchresult", {}).get("count", "0")
                    print(f"  结果: 找到 {len(id_list)} 个PMID (总数: {count})")
                    
                    if id_list:
                        print(f"  PMIDs: {id_list[:5]}")
                        target_pmid = "41188603"
                        if target_pmid in id_list:
                            print(f"  [OK] 找到目标PMID: {target_pmid}")
                        else:
                            print(f"  [FAIL] 未找到目标PMID: {target_pmid}")
                    else:
                        print(f"  [FAIL] 未找到任何结果")
                else:
                    print(f"  [FAIL] 请求失败: {response.status_code}")
                    print(f"  响应: {response.text[:200]}")
            except Exception as e:
                print(f"  [ERROR] 错误: {str(e)}")
            
            # 避免请求过快
            await asyncio.sleep(0.3)

if __name__ == "__main__":
    asyncio.run(test_queries())

