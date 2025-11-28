"""测试修复后的检索"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.pubmed_service import PubMedService

async def test_fixed_search():
    """测试修复后的检索"""
    service = PubMedService()
    
    keywords = {
        "title": "A focus shift from sarcopenia to muscle health in the Asian Working Group for Sarcopenia 2025 Consensus Update",
        "authors": ["Chen, L. K.", "Hsiao, F. Y.", "Akishita, N.", "Tan, M. P.", "Won, C. W.", "Yamada, M.", "Woo, J.", "Arai, H."],
        "journal": "Nature Aging",
        "year": 2025,
        "volume": "5",
        "issue": "11",
        "pages": "2164-2175",
    }
    
    print("=" * 80)
    print("测试修复后的检索")
    print("=" * 80)
    
    # 测试完整的检索流程
    print("\n【完整检索流程】")
    articles = await service.search_articles(keywords, use_smart_matching=False)
    
    print(f"\n检索结果: 找到 {len(articles)} 篇文章")
    
    target_pmid = "41188603"
    found = False
    for article in articles:
        if article.get("pmid") == target_pmid:
            found = True
            print(f"\n[OK] 找到目标文章:")
            print(f"  PMID: {article.get('pmid')}")
            print(f"  标题: {article.get('title', 'N/A')[:80]}...")
            print(f"  作者: {article.get('authors', [])[:3]}")
            break
    
    if not found:
        print(f"\n[FAIL] 未找到目标文章 (PMID: {target_pmid})")
        if articles:
            print(f"\n找到的其他文章:")
            for i, article in enumerate(articles[:3], 1):
                print(f"  [{i}] PMID={article.get('pmid')}, 标题={article.get('title', 'N/A')[:60]}...")

if __name__ == "__main__":
    asyncio.run(test_fixed_search())


