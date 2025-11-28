"""测试标题中的2025是否导致问题"""
import asyncio
import httpx

async def test_title_with_2025():
    """测试标题中的2025"""
    PUBMED_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    
    # 测试不同的标题变体
    title_variants = [
        "A focus shift from sarcopenia to muscle health in the Asian Working Group for Sarcopenia 2025 Consensus Update",
        "A focus shift from sarcopenia to muscle health in the Asian Working Group for Sarcopenia Consensus Update",
        "focus shift from sarcopenia to muscle health in the Asian Working Group for Sarcopenia Consensus Update",
        "sarcopenia muscle health Asian Working Group Sarcopenia Consensus Update",
        "sarcopenia muscle health Asian Working Group Sarcopenia",
    ]
    
    async with httpx.AsyncClient() as client:
        for i, title in enumerate(title_variants, 1):
            print(f"\n【测试{i}】标题: {title[:60]}...")
            
            # 测试精确匹配
            try:
                search_url = f"{PUBMED_BASE_URL}/esearch.fcgi"
                params = {
                    "db": "pubmed",
                    "term": f'"{title}"[Title]',
                    "retmode": "json",
                    "retmax": 5,
                }
                
                response = await client.get(search_url, params=params, timeout=10.0)
                
                if response.status_code == 200:
                    data = response.json()
                    id_list = data.get("esearchresult", {}).get("idlist", [])
                    count = data.get("esearchresult", {}).get("count", "0")
                    print(f"  精确匹配: 找到 {len(id_list)} 个PMID (总数: {count})")
                    
                    target_pmid = "41188603"
                    if target_pmid in id_list:
                        print(f"  [OK] 找到目标PMID")
                    else:
                        print(f"  [FAIL] 未找到目标PMID")
                else:
                    print(f"  [ERROR] 请求失败: {response.status_code}")
            except Exception as e:
                print(f"  [ERROR] 错误: {str(e)}")
            
            # 测试模糊匹配（关键词）
            try:
                title_words = title.split()
                if len(title_words) > 0:
                    # 只使用前10个词
                    key_words = title_words[:10]
                    search_url = f"{PUBMED_BASE_URL}/esearch.fcgi"
                    params = {
                        "db": "pubmed",
                        "term": f'({" AND ".join(key_words)})[Title]',
                        "retmode": "json",
                        "retmax": 5,
                    }
                    
                    response = await client.get(search_url, params=params, timeout=10.0)
                    
                    if response.status_code == 200:
                        data = response.json()
                        id_list = data.get("esearchresult", {}).get("idlist", [])
                        count = data.get("esearchresult", {}).get("count", "0")
                        print(f"  模糊匹配（前10词）: 找到 {len(id_list)} 个PMID (总数: {count})")
                        
                        target_pmid = "41188603"
                        if target_pmid in id_list:
                            print(f"  [OK] 找到目标PMID")
                        else:
                            print(f"  [FAIL] 未找到目标PMID")
            except Exception as e:
                print(f"  [ERROR] 错误: {str(e)}")
            
            await asyncio.sleep(0.3)

if __name__ == "__main__":
    asyncio.run(test_title_with_2025())


