"""测试修复后模糊搜索的实际查询字符串"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.pubmed_service import PubMedService

async def test_query_strings():
    """测试实际查询字符串"""
    service = PubMedService()
    
    title = "A focus shift from sarcopenia to muscle health in the Asian Working Group for Sarcopenia 2025 Consensus Update"
    first_author = "Chen, L. K."
    journal = "Nature Aging"
    year = 2025
    
    print("=" * 80)
    print("测试模糊搜索的实际查询字符串")
    print("=" * 80)
    print(f"\n输入标题: {title}")
    print(f"第一作者: {first_author}")
    print(f"期刊: {journal}")
    print(f"年份: {year}")
    print("\n" + "=" * 80)
    
    # 模拟 search_by_title 方法中的逻辑
    title_clean = title.rstrip('.')
    print(f"\n【步骤1】清理后的标题: {title_clean}")
    
    # 模糊匹配的关键词提取
    title_words = title_clean.split()
    print(f"  标题词数: {len(title_words)} 个词")
    print(f"  所有词: {title_words}")
    
    stop_words = {'the', 'a', 'an', 'and', 'or', 'for', 'of', 'in', 'on', 'at', 'to', 'by', 'with', 'is', 'are', 'was', 'were', 'from'}
    keywords_list = [w for w in title_words if w.lower() not in stop_words and len(w) > 2]
    print(f"\n【步骤2】去除停用词后的关键词:")
    print(f"  关键词数: {len(keywords_list)} 个")
    print(f"  关键词列表: {keywords_list}")
    
    # 限制关键词数量
    num_keywords = min(15, len(keywords_list))
    final_keywords = keywords_list[:num_keywords]
    print(f"\n【步骤3】限制后的关键词（最多15个）:")
    print(f"  使用关键词数: {len(final_keywords)} 个")
    print(f"  最终关键词: {final_keywords}")
    
    # 构建查询
    title_query = f'({" AND ".join(final_keywords)})[Title]'
    print(f"\n【步骤4】标题查询字符串:")
    print(f"  {title_query}")
    
    # 处理作者
    processed_author = first_author.split(",")[0].strip() if "," in first_author else first_author.strip()
    print(f"\n【步骤5】作者处理:")
    print(f"  原始作者: {first_author}")
    print(f"  处理后作者: {processed_author}")
    author_query = f'{processed_author}[Author]'
    print(f"  作者查询: {author_query}")
    
    # 处理期刊
    journal_words = journal.split()
    if len(journal_words) > 1:
        journal_query = f'({" AND ".join(journal_words)})[Journal]'
    else:
        journal_query = f'{journal}[Journal]'
    print(f"\n【步骤6】期刊查询:")
    print(f"  {journal_query}")
    
    # 年份查询
    year_query = f'{year}[Publication Date]'
    print(f"\n【步骤7】年份查询:")
    print(f"  {year_query}")
    
    # 组合查询示例
    print(f"\n【步骤8】组合查询示例:")
    print(f"\n1. 标题+作者+期刊+年份（模糊匹配）:")
    combined_query1 = f'{title_query} AND {author_query} AND {journal_query} AND {year_query}'
    print(f"  {combined_query1}")
    
    print(f"\n2. 标题+期刊+年份（模糊匹配）:")
    combined_query2 = f'{title_query} AND {journal_query} AND {year_query}'
    print(f"  {combined_query2}")
    
    print(f"\n3. 标题+作者（模糊匹配）:")
    combined_query3 = f'{title_query} AND {author_query}'
    print(f"  {combined_query3}")
    
    print(f"\n4. 只标题（模糊匹配）:")
    print(f"  {title_query}")
    
    # 实际测试
    print(f"\n" + "=" * 80)
    print("实际测试检索")
    print("=" * 80)
    
    # 测试标题模糊匹配
    print(f"\n【测试1】标题模糊匹配（exact_match=False）")
    pmids = await service.search_by_title(title, exact_match=False)
    print(f"  结果: 找到 {len(pmids)} 个PMID")
    if pmids:
        print(f"  PMIDs: {pmids[:5]}")
        target_pmid = "41188603"
        if target_pmid in pmids:
            print(f"  [OK] 找到目标PMID: {target_pmid}")
    
    # 测试标题+期刊+年份模糊匹配
    print(f"\n【测试2】标题+期刊+年份模糊匹配")
    pmids = await service.search_by_title(title, journal=journal, year=year, exact_match=False)
    print(f"  结果: 找到 {len(pmids)} 个PMID")
    if pmids:
        print(f"  PMIDs: {pmids[:5]}")
        target_pmid = "41188603"
        if target_pmid in pmids:
            print(f"  [OK] 找到目标PMID: {target_pmid}")

if __name__ == "__main__":
    asyncio.run(test_query_strings())


