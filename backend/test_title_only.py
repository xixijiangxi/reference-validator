"""测试标题检索失败的原因"""
import asyncio
import httpx
import json

async def test_title_queries():
    """测试标题相关的查询"""
    PUBMED_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    
    title = "A focus shift from sarcopenia to muscle health in the Asian Working Group for Sarcopenia 2025 Consensus Update"
    title_clean = title.rstrip('.')
    
    # 测试不同长度的标题
    title_parts = title_clean.split()
    
    queries = [
        # 测试完整标题
        {
            "name": "完整标题（精确匹配）",
            "term": f'"{title_clean}"[Title]',
        },
        # 测试前5个词
        {
            "name": "前5个词",
            "term": f'({" AND ".join(title_parts[:5])})[Title]',
        },
        # 测试前10个词
        {
            "name": "前10个词",
            "term": f'({" AND ".join(title_parts[:10])})[Title]',
        },
        # 测试前15个词
        {
            "name": "前15个词",
            "term": f'({" AND ".join(title_parts[:15])})[Title]',
        },
        # 测试核心关键词
        {
            "name": "核心关键词（sarcopenia 2025）",
            "term": f'(sarcopenia AND 2025)[Title]',
        },
        # 测试去除停用词后的关键词
        {
            "name": "去除停用词后的关键词",
            "term": f'({" AND ".join([w for w in title_parts if w.lower() not in {"the", "a", "an", "and", "or", "for", "of", "in", "on", "at", "to", "by", "with", "is", "are", "was", "were"} and len(w) > 2][:10])})[Title]',
        },
        # 测试只搜索"sarcopenia"
        {
            "name": "只搜索sarcopenia",
            "term": f'sarcopenia[Title]',
        },
        # 测试搜索"sarcopenia"和"2025"
        {
            "name": "sarcopenia + 2025",
            "term": f'sarcopenia[Title] AND 2025[Publication Date]',
        },
    ]
    
    async with httpx.AsyncClient() as client:
        for query_info in queries:
            print(f"\n【{query_info['name']}】")
            print(f"  查询: {query_info['term'][:120]}...")
            
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
            
            await asyncio.sleep(0.3)

if __name__ == "__main__":
    asyncio.run(test_title_queries())


