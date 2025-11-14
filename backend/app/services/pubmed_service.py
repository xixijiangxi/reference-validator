import httpx
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv
import logging
from pathlib import Path

# 加载 .env 文件
env_path = Path(__file__).parent.parent.parent / '.env'
if not env_path.exists():
    env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

PUBMED_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
PUBMED_EMAIL = os.getenv("PUBMED_EMAIL", "")

logger = logging.getLogger(__name__)


class PubMedService:
    """PubMed API服务"""
    
    def __init__(self):
        self.email = PUBMED_EMAIL
    
    async def search_by_doi(self, doi: str) -> Optional[str]:
        """通过DOI搜索PMID"""
        if not doi:
            return None
        
        # 清理DOI格式
        doi = doi.strip().replace("https://doi.org/", "").replace("doi:", "").strip()
        
        logger.info(f"  通过 DOI 搜索: {doi}")
        
        async with httpx.AsyncClient() as client:
            try:
                # 使用esearch搜索
                search_url = f"{PUBMED_BASE_URL}/esearch.fcgi"
                params = {
                    "db": "pubmed",
                    "term": f"{doi}[DOI]",
                    "retmode": "json",
                    "retmax": 1,
                }
                
                logger.info(f"  发送请求: GET {search_url}")
                logger.info(f"  请求参数: {params}")
                
                response = await client.get(search_url, params=params, timeout=10.0)
                
                logger.info(f"  响应状态码: {response.status_code}")
                logger.info(f"  响应内容: {response.text[:300]}...")
                
                if response.status_code == 200:
                    data = response.json()
                    id_list = data.get("esearchresult", {}).get("idlist", [])
                    if id_list:
                        logger.info(f"  找到 PMID: {id_list[0]}")
                        return id_list[0]
                    else:
                        logger.info(f"  未找到匹配的 PMID")
            except Exception as e:
                logger.error(f"DOI搜索出错: {str(e)}", exc_info=True)
        
        return None
    
    async def search_by_title(self, title: str, author: Optional[str] = None, 
                             journal: Optional[str] = None, year: Optional[int] = None,
                             exact_match: bool = True) -> List[str]:
        """通过标题搜索PMID列表
        
        Args:
            title: 文章标题
            author: 作者（可选）
            journal: 期刊名称（可选）
            year: 年份（可选）
            exact_match: 是否使用完全匹配（默认True，使用引号；False时使用关键词匹配）
        """
        if not title:
            return []
        
        # 清理标题：去除末尾句号，因为PubMed可能存储时没有句号
        title_clean = title.rstrip('.')
        
        # 构建搜索查询
        if exact_match:
            query_parts = [f'"{title_clean}"[Title]']
        else:
            # 部分匹配：使用关键词，用 AND 连接
            title_words = title_clean.split()
            query_parts = [f'({" AND ".join(title_words)})[Title]']
        
        if author:
            # 只取第一作者
            first_author = author.split(",")[0].strip() if "," in author else author.strip()
            query_parts.append(f'"{first_author}"[Author]')
        
        if journal:
            query_parts.append(f'"{journal}"[Journal]')
        
        if year:
            query_parts.append(f'{year}[Publication Date]')
        
        query = " AND ".join(query_parts)
        
        logger.info(f"  PubMed 搜索查询: {query}")
        
        async with httpx.AsyncClient() as client:
            try:
                search_url = f"{PUBMED_BASE_URL}/esearch.fcgi"
                params = {
                    "db": "pubmed",
                    "term": query,
                    "retmode": "json",
                    "retmax": 20,
        
                }
                
                logger.info(f"  发送请求: GET {search_url}")
                logger.info(f"  请求参数: {params}")
                
                response = await client.get(search_url, params=params, timeout=10.0)
                
                logger.info(f"  响应状态码: {response.status_code}")
                logger.info(f"  响应内容: {response.text[:500]}...")
                
                if response.status_code == 200:
                    data = response.json()
                    id_list = data.get("esearchresult", {}).get("idlist", [])
                    logger.info(f"  找到 {len(id_list)} 个 PMID")
                    return id_list
            except Exception as e:
                logger.error(f"标题搜索出错: {str(e)}", exc_info=True)
        
        return []
    
    async def fetch_article_details(self, pmid: str) -> Optional[Dict[str, Any]]:
        """获取文章详细信息"""
        logger.info(f"  获取文章详情: PMID={pmid}")
        
        async with httpx.AsyncClient() as client:
            try:
                fetch_url = f"{PUBMED_BASE_URL}/efetch.fcgi"
                params = {
                    "db": "pubmed",
                    "id": pmid,
                    "retmode": "xml",
                    "email": self.email
                }
                
                logger.info(f"  发送请求: GET {fetch_url}")
                logger.info(f"  请求参数: {params}")
                
                response = await client.get(fetch_url, params=params, timeout=10.0)
                
                logger.info(f"  响应状态码: {response.status_code}")
                logger.info(f"  响应内容长度: {len(response.text)} 字符")
                
                if response.status_code == 200:
                    article = self._parse_xml(response.text)
                    if article:
                        logger.info(f"  解析成功: 标题={article.get('title', 'N/A')[:60]}...")
                    return article
            except Exception as e:
                logger.error(f"获取文章详情出错: {str(e)}", exc_info=True)
        
        return None
    
    def _parse_xml(self, xml_content: str) -> Dict[str, Any]:
        """解析PubMed XML响应"""
        try:
            root = ET.fromstring(xml_content)
            article = root.find(".//PubmedArticle")
            if article is None:
                return {}
            
            medline = article.find(".//MedlineCitation")
            if medline is None:
                return {}
            
            pmid_elem = medline.find(".//PMID")
            pmid = pmid_elem.text if pmid_elem is not None else None
            
            # 标题
            title_elem = medline.find(".//ArticleTitle")
            title = title_elem.text if title_elem is not None else None
            
            # 作者
            authors = []
            author_list = medline.find(".//AuthorList")
            if author_list is not None:
                for author in author_list.findall(".//Author"):
                    last_name = author.find(".//LastName")
                    first_name = author.find(".//ForeName")
                    if last_name is not None:
                        name = last_name.text
                        if first_name is not None:
                            name += f", {first_name.text}"
                        authors.append(name)
            
            # 期刊
            journal_elem = medline.find(".//Journal/Title")
            journal = journal_elem.text if journal_elem is not None else None
            
            # 年份
            pub_date = medline.find(".//PubDate")
            year = None
            if pub_date is not None:
                year_elem = pub_date.find(".//Year")
                if year_elem is not None:
                    try:
                        year = int(year_elem.text)
                    except:
                        pass
            
            # 卷期
            volume_elem = medline.find(".//Volume")
            volume = volume_elem.text if volume_elem is not None else None
            
            issue_elem = medline.find(".//Issue")
            issue = issue_elem.text if issue_elem is not None else None
            
            # 页码
            pagination = medline.find(".//Pagination")
            pages = None
            if pagination is not None:
                start_page = pagination.find(".//StartPage")
                end_page = pagination.find(".//EndPage")
                if start_page is not None:
                    pages = start_page.text
                    if end_page is not None:
                        pages += f"-{end_page.text}"
            
            # DOI
            article_id_list = medline.find(".//ArticleIdList")
            doi = None
            if article_id_list is not None:
                for article_id in article_id_list.findall(".//ArticleId"):
                    if article_id.get("IdType") == "doi":
                        doi = article_id.text
                        break
            
            # 摘要
            abstract_elem = medline.find(".//Abstract/AbstractText")
            abstract = abstract_elem.text if abstract_elem is not None else None
            
            return {
                "pmid": pmid,
                "title": title,
                "authors": authors,
                "journal": journal,
                "year": year,
                "volume": volume,
                "issue": issue,
                "pages": pages,
                "doi": doi,
                "abstract": abstract
            }
        except Exception as e:
            print(f"解析XML出错: {str(e)}")
            return {}
    
    async def search_articles(self, keywords: Dict[str, Any]) -> List[Dict[str, Any]]:
        """根据关键词搜索文章，按优先级顺序，使用优化的检索策略"""
        logger.info("*" * 80)
        logger.info("开始 PubMed 检索（优化策略）")
        logger.info(f"检索关键词: {keywords}")
        
        # 导入相似度服务（延迟导入避免循环依赖）
        from app.services.similarity_service import SimilarityService
        similarity_service = SimilarityService()
        
        results = []
        seen_pmids = set()
        
        # 优先级0: PMID直接搜索（最可靠）
        if keywords.get("pmid"):
            pmid = str(keywords["pmid"]).strip()
            logger.info(f"[优先级0] 使用 PMID 直接检索: {pmid}")
            article = await self.fetch_article_details(pmid)
            if article:
                article["pmid"] = pmid
                results.append(article)
                seen_pmids.add(pmid)
                logger.info(f"  直接找到文章: {article.get('title', 'N/A')[:80]}...")
                logger.info(f"PubMed 检索完成，共找到 {len(results)} 篇文章")
                return results
            else:
                logger.info("  未找到对应的文章")
        
        # 优先级1: DOI搜索
        if keywords.get("doi"):
            logger.info(f"[优先级1] 使用 DOI 检索: {keywords['doi']}")
            pmid = await self.search_by_doi(keywords["doi"])
            if pmid and pmid not in seen_pmids:
                logger.info(f"  找到 PMID: {pmid}")
                article = await self.fetch_article_details(pmid)
                if article:
                    article["pmid"] = pmid
                    results.append(article)
                    seen_pmids.add(pmid)
                    logger.info(f"  检索到文章: {article.get('title', 'N/A')[:80]}...")
                    logger.info(f"PubMed 检索完成，共找到 {len(results)} 篇文章")
                    return results
            else:
                logger.info("  未找到匹配的 PMID")
        
        # 优先级2: 精确匹配 + 多字段组合（按可靠性排序）
        title = keywords.get("title")
        first_author = None
        if keywords.get("authors"):
            first_author = keywords["authors"][0] if isinstance(keywords["authors"], list) else keywords["authors"]
        journal = keywords.get("journal")
        year = keywords.get("year")
        
        if title:
            # 定义精确匹配策略（按可靠性从高到低）
            exact_strategies = [
                ("标题+作者+期刊+年份", title, first_author, journal, year),
                ("标题+期刊+年份", title, None, journal, year),
                ("标题+作者", title, first_author, None, None),
                ("标题", title, None, None, None),
            ]
            
            for strategy_name, t, a, j, y in exact_strategies:
                # 跳过无效策略（缺少必要字段）
                if strategy_name == "标题+作者+期刊+年份" and not (a and j and y):
                    continue
                if strategy_name == "标题+期刊+年份" and not (j and y):
                    continue
                if strategy_name == "标题+作者" and not a:
                    continue
                
                logger.info(f"[优先级2] {strategy_name}（精确匹配）")
                pmids = await self.search_by_title(t, author=a, journal=j, year=y, exact_match=True)
                logger.info(f"  找到 {len(pmids)} 个 PMID: {pmids}")
                
                for pmid in pmids:
                    if pmid not in seen_pmids:
                        article = await self.fetch_article_details(pmid)
                        if article:
                            article["pmid"] = pmid
                            results.append(article)
                            seen_pmids.add(pmid)
                            logger.info(f"  检索到文章 [{pmid}]: {article.get('title', 'N/A')[:60]}...")
                
                # 如果找到结果，检查是否有高置信度匹配
                if results:
                    # 计算相似度并检查是否有高置信度结果
                    scored_results = []
                    for article in results:
                        article_keywords = {
                            "title": article.get("title"),
                            "authors": article.get("authors", []),
                            "journal": article.get("journal"),
                            "year": article.get("year"),
                            "volume": article.get("volume"),
                            "issue": article.get("issue"),
                            "pages": article.get("pages"),
                            "pmid": article.get("pmid"),
                            "doi": article.get("doi")
                        }
                        similarity = similarity_service.calculate_similarity(keywords, article_keywords)
                        scored_results.append((similarity, article))
                    
                    # 按相似度排序
                    scored_results.sort(key=lambda x: x[0], reverse=True)
                    
                    # 如果有高置信度结果（相似度>0.9），只返回最高分的一个
                    if scored_results and scored_results[0][0] > 0.9:
                        logger.info(f"  找到高置信度匹配（相似度={scored_results[0][0]:.4f}），返回最佳匹配")
                        return [scored_results[0][1]]
                    
                    # 如果结果唯一，直接返回
                    if len(results) == 1:
                        logger.info(f"PubMed 检索完成，找到唯一匹配文章")
                        return results
                    
                    # 如果找到多个结果，继续尝试更精确的策略
                    break
            
            # 如果精确匹配失败，且标题很长，尝试使用前几个词
            if len(results) == 0:
                title_words = title.split()
                if len(title_words) > 15:  # 标题超过15个词
                    logger.info(f"[优先级2b] 标题过长（{len(title_words)}个词），尝试使用前15个词")
                    short_title = " ".join(title_words[:15])
                    pmids = await self.search_by_title(short_title, exact_match=True)
                    if journal:
                        pmids_with_journal = await self.search_by_title(short_title, journal=journal, exact_match=True)
                        pmids = list(set(pmids + pmids_with_journal))
                    logger.info(f"  找到 {len(pmids)} 个 PMID: {pmids}")
                    for pmid in pmids:
                        if pmid not in seen_pmids:
                            article = await self.fetch_article_details(pmid)
                            if article:
                                article["pmid"] = pmid
                                results.append(article)
                                seen_pmids.add(pmid)
                                logger.info(f"  检索到文章 [{pmid}]: {article.get('title', 'N/A')[:60]}...")
        
        # 优先级3: 模糊匹配 + 多字段组合（如果精确匹配未找到高置信度结果）
        if title and len(results) == 0:
            logger.info(f"[优先级3] 精确匹配未找到结果，尝试模糊匹配")
            
            # 提取标题关键词
            title_words = title.split()
            stop_words = {'the', 'a', 'an', 'and', 'or', 'for', 'of', 'in', 'on', 'at', 'to', 'by', 'with', 'is', 'are', 'was', 'were'}
            keywords_list = [w for w in title_words if w.lower() not in stop_words and len(w) > 2]
            
            if len(keywords_list) >= 5:
                num_keywords = min(10, len(keywords_list))
                key_title = " ".join(keywords_list[:num_keywords])
                logger.info(f"  使用关键词: {key_title[:80]}...")
                
                # 模糊匹配策略（按可靠性从高到低）
                fuzzy_strategies = [
                    ("关键词+作者+期刊+年份", key_title, first_author, journal, year),
                    ("关键词+期刊+年份", key_title, None, journal, year),
                    ("关键词+作者", key_title, first_author, None, None),
                    ("关键词", key_title, None, None, None),
                ]
                
                for strategy_name, t, a, j, y in fuzzy_strategies:
                    if strategy_name == "关键词+作者+期刊+年份" and not (a and j and y):
                        continue
                    if strategy_name == "关键词+期刊+年份" and not (j and y):
                        continue
                    if strategy_name == "关键词+作者" and not a:
                        continue
                    
                    logger.info(f"  策略: {strategy_name}")
                    pmids = await self.search_by_title(t, author=a, journal=j, year=y, exact_match=False)
                    logger.info(f"    找到 {len(pmids)} 个 PMID")
                    
                    for pmid in pmids:
                        if pmid not in seen_pmids:
                            article = await self.fetch_article_details(pmid)
                            if article:
                                article["pmid"] = pmid
                                results.append(article)
                                seen_pmids.add(pmid)
                                logger.info(f"    检索到文章 [{pmid}]: {article.get('title', 'N/A')[:60]}...")
                    
                    if results:
                        break
        
        # 优先级4: 相似度排序和智能返回
        if results:
            scored_results = []
            for article in results:
                article_keywords = {
                    "title": article.get("title"),
                    "authors": article.get("authors", []),
                    "journal": article.get("journal"),
                    "year": article.get("year"),
                    "volume": article.get("volume"),
                    "issue": article.get("issue"),
                    "pages": article.get("pages"),
                    "pmid": article.get("pmid"),
                    "doi": article.get("doi")
                }
                similarity = similarity_service.calculate_similarity(keywords, article_keywords)
                scored_results.append((similarity, article))
            
            # 按相似度排序
            scored_results.sort(key=lambda x: x[0], reverse=True)
            
            # 智能返回策略
            if scored_results:
                best_score = scored_results[0][0]
                logger.info(f"  最佳相似度: {best_score:.4f}")
                
                if best_score > 0.9:
                    # 高置信度：返回1篇
                    logger.info(f"  高置信度（>0.9），返回最佳匹配")
                    return [scored_results[0][1]]
                elif best_score > 0.7:
                    # 中等置信度：返回1-2篇
                    logger.info(f"  中等置信度（0.7-0.9），返回前2篇")
                    return [article for _, article in scored_results[:2]]
                else:
                    # 低置信度：返回最多3篇
                    logger.info(f"  低置信度（<0.7），返回前3篇")
                    return [article for _, article in scored_results[:3]]
        
        logger.info(f"PubMed 检索完成，共找到 {len(results)} 篇文章")
        return results

