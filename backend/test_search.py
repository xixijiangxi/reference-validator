"""测试特定参考文献的检索过程"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.pubmed_service import PubMedService

async def test_search():
    """测试检索"""
    service = PubMedService()
    
    # 模拟用户输入的关键词
    keywords = {
        "title": "A focus shift from sarcopenia to muscle health in the Asian Working Group for Sarcopenia 2025 Consensus Update",
        "authors": ["Chen, L. K.", "Hsiao, F. Y.", "Akishita, N.", "Tan, M. P.", "Won, C. W.", "Yamada, M.", "Woo, J.", "Arai, H."],
        "journal": "Nature Aging",
        "year": 2025,
        "volume": "5",
        "issue": "11",
        "pages": "2164-2175",
        "doi": None,
        "pmid": None
    }
    
    print("=" * 80)
    print("测试检索关键词:")
    print(f"  标题: {keywords['title']}")
    print(f"  第一作者: {keywords['authors'][0]}")
    print(f"  期刊: {keywords['journal']}")
    print(f"  年份: {keywords['year']}")
    print("=" * 80)
    
    # 测试1: 标题精确匹配
    print("\n【测试1】标题精确匹配")
    title = keywords['title']
    pmids = await service.search_by_title(title, exact_match=True)
    print(f"  结果: 找到 {len(pmids)} 个PMID")
    if pmids:
        print(f"  PMIDs: {pmids[:5]}")
    
    # 测试2: 标题+作者+期刊+年份（精确匹配）
    print("\n【测试2】标题+作者+期刊+年份（精确匹配）")
    first_author = keywords['authors'][0]  # "Chen, L. K."
    print(f"  第一作者（原始）: {first_author}")
    # 模拟代码中的处理
    processed_author = first_author.split(",")[0].strip() if "," in first_author else first_author.strip()
    print(f"  第一作者（处理后）: {processed_author}")
    pmids = await service.search_by_title(
        title, 
        author=first_author, 
        journal=keywords['journal'], 
        year=keywords['year'],
        exact_match=True
    )
    print(f"  结果: 找到 {len(pmids)} 个PMID")
    if pmids:
        print(f"  PMIDs: {pmids[:5]}")
    
    # 测试3: 标题模糊匹配（关键词）
    print("\n【测试3】标题模糊匹配（关键词）")
    pmids = await service.search_by_title(title, exact_match=False)
    print(f"  结果: 找到 {len(pmids)} 个PMID")
    if pmids:
        print(f"  PMIDs: {pmids[:5]}")
        # 检查是否包含目标PMID
        target_pmid = "41188603"
        if target_pmid in pmids:
            print(f"  ✅ 找到目标PMID: {target_pmid}")
        else:
            print(f"  ❌ 未找到目标PMID: {target_pmid}")
    
    # 测试4: 标题+作者+期刊+年份（模糊匹配）
    print("\n【测试4】标题+作者+期刊+年份（模糊匹配）")
    pmids = await service.search_by_title(
        title, 
        author=first_author, 
        journal=keywords['journal'], 
        year=keywords['year'],
        exact_match=False
    )
    print(f"  结果: 找到 {len(pmids)} 个PMID")
    if pmids:
        print(f"  PMIDs: {pmids[:5]}")
        target_pmid = "41188603"
        if target_pmid in pmids:
            print(f"  ✅ 找到目标PMID: {target_pmid}")
        else:
            print(f"  ❌ 未找到目标PMID: {target_pmid}")
    
    # 测试5: 只使用标题关键词（去除停用词）
    print("\n【测试5】标题关键词（去除停用词）")
    title_words = title.split()
    stop_words = {'the', 'a', 'an', 'and', 'or', 'for', 'of', 'in', 'on', 'at', 'to', 'by', 'with', 'is', 'are', 'was', 'were'}
    keywords_list = [w for w in title_words if w.lower() not in stop_words and len(w) > 2]
    key_title = " ".join(keywords_list[:10])
    print(f"  关键词: {key_title}")
    pmids = await service.search_by_title(key_title, exact_match=False)
    print(f"  结果: 找到 {len(pmids)} 个PMID")
    if pmids:
        print(f"  PMIDs: {pmids[:5]}")
        target_pmid = "41188603"
        if target_pmid in pmids:
            print(f"  ✅ 找到目标PMID: {target_pmid}")
        else:
            print(f"  ❌ 未找到目标PMID: {target_pmid}")
    
    # 测试6: 关键词+期刊+年份（模糊匹配）
    print("\n【测试6】关键词+期刊+年份（模糊匹配）")
    pmids = await service.search_by_title(
        key_title, 
        journal=keywords['journal'], 
        year=keywords['year'],
        exact_match=False
    )
    print(f"  结果: 找到 {len(pmids)} 个PMID")
    if pmids:
        print(f"  PMIDs: {pmids[:5]}")
        target_pmid = "41188603"
        if target_pmid in pmids:
            print(f"  ✅ 找到目标PMID: {target_pmid}")
        else:
            print(f"  ❌ 未找到目标PMID: {target_pmid}")
    
    # 测试7: 检查目标文章的实际信息
    print("\n【测试7】直接获取目标文章信息（PMID: 41188603）")
    target_article = await service.fetch_article_details("41188603")
    if target_article:
        print(f"  标题: {target_article.get('title', 'N/A')}")
        print(f"  作者: {target_article.get('authors', [])[:3]}")
        print(f"  期刊: {target_article.get('journal', 'N/A')}")
        print(f"  年份: {target_article.get('year', 'N/A')}")
        print(f"  DOI: {target_article.get('doi', 'N/A')}")
        
        # 比较标题
        pubmed_title = target_article.get('title', '')
        input_title = keywords['title']
        print(f"\n  标题比较:")
        print(f"    输入: {input_title[:80]}...")
        print(f"    PubMed: {pubmed_title[:80]}...")
        print(f"    是否相同: {input_title.lower().strip() == pubmed_title.lower().strip()}")
        
        # 比较作者
        pubmed_authors = target_article.get('authors', [])
        input_first_author = keywords['authors'][0]
        print(f"\n  第一作者比较:")
        print(f"    输入: {input_first_author}")
        if pubmed_authors:
            print(f"    PubMed: {pubmed_authors[0]}")
            # 标准化比较
            input_normalized = input_first_author.lower().replace(',', '').replace('.', '').strip()
            pubmed_normalized = pubmed_authors[0].lower().replace(',', '').replace('.', '').strip()
            print(f"    标准化后是否相似: {input_normalized.startswith(pubmed_normalized.split()[0]) if pubmed_normalized.split() else False}")
    else:
        print("  ❌ 无法获取文章信息")

if __name__ == "__main__":
    asyncio.run(test_search())


