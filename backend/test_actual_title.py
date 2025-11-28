"""检查PubMed中文章的实际标题"""
import asyncio
import httpx
import xml.etree.ElementTree as ET

async def check_actual_title():
    """检查目标文章的实际标题"""
    PUBMED_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    target_pmid = "41188603"
    
    async with httpx.AsyncClient() as client:
        try:
            fetch_url = f"{PUBMED_BASE_URL}/efetch.fcgi"
            params = {
                "db": "pubmed",
                "id": target_pmid,
                "retmode": "xml",
            }
            
            response = await client.get(fetch_url, params=params, timeout=10.0)
            
            if response.status_code == 200:
                root = ET.fromstring(response.text)
                article = root.find(".//PubmedArticle")
                if article is not None:
                    medline = article.find(".//MedlineCitation")
                    if medline is not None:
                        title_elem = medline.find(".//ArticleTitle")
                        if title_elem is not None:
                            actual_title = title_elem.text
                            print(f"PubMed中的实际标题:")
                            print(f"  {actual_title}")
                            print(f"\n标题长度: {len(actual_title)} 字符")
                            print(f"标题词数: {len(actual_title.split())} 个词")
                            
                            # 比较输入标题
                            input_title = "A focus shift from sarcopenia to muscle health in the Asian Working Group for Sarcopenia 2025 Consensus Update"
                            print(f"\n输入标题:")
                            print(f"  {input_title}")
                            print(f"\n标题比较:")
                            print(f"  完全相同: {input_title == actual_title}")
                            print(f"  去除末尾句号后相同: {input_title.rstrip('.') == actual_title.rstrip('.')}")
                            print(f"  忽略大小写相同: {input_title.lower() == actual_title.lower()}")
                            
                            # 检查标题中的特殊字符
                            print(f"\n特殊字符检查:")
                            print(f"  输入标题中的数字: {[c for c in input_title if c.isdigit()]}")
                            print(f"  实际标题中的数字: {[c for c in actual_title if c.isdigit()]}")
                            
                            # 测试使用实际标题搜索
                            print(f"\n使用实际标题搜索:")
                            search_url = f"{PUBMED_BASE_URL}/esearch.fcgi"
                            search_params = {
                                "db": "pubmed",
                                "term": f'"{actual_title}"[Title]',
                                "retmode": "json",
                                "retmax": 5,
                            }
                            search_response = await client.get(search_url, params=search_params, timeout=10.0)
                            if search_response.status_code == 200:
                                search_data = search_response.json()
                                search_ids = search_data.get("esearchresult", {}).get("idlist", [])
                                print(f"  结果: 找到 {len(search_ids)} 个PMID")
                                if target_pmid in search_ids:
                                    print(f"  [OK] 找到目标PMID")
                                else:
                                    print(f"  [FAIL] 未找到目标PMID")
        except Exception as e:
            print(f"错误: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_actual_title())


