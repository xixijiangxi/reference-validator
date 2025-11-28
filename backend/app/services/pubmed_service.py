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
                    "sort": "relevance",  # 按最佳匹配排序
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
                             exact_match: bool = True, use_quotes: Optional[bool] = None) -> List[str]:
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
            # 精确匹配：根据 use_quotes 参数决定是否使用引号
            # use_quotes=None 时默认使用引号（保持向后兼容）
            if use_quotes is None or use_quotes:
                query_parts = [f'"{title_clean}"[Title]']
            else:
                # 不带引号的精确匹配（更灵活，能匹配略有差异的标题）
                query_parts = [f'{title_clean}[Title]']
        else:
            # 部分匹配：使用关键词，关键词之间用空格分隔（不用AND）
            # 去除停用词，避免查询过长导致失败
            title_words = title_clean.split()
            stop_words = {'the', 'a', 'an', 'and', 'or', 'for', 'of', 'in', 'on', 'at', 'to', 'by', 'with', 'is', 'are', 'was', 'were', 'from'}
            keywords_list = [w for w in title_words if w.lower() not in stop_words and len(w) > 2]
            
            # 如果去除停用词后还有足够的关键词，使用关键词；否则使用所有词
            if len(keywords_list) >= 3:
                # 限制关键词数量，避免查询过长（最多15个关键词）
                num_keywords = min(15, len(keywords_list))
                # 关键词之间用空格分隔，不用AND
                query_parts = [f'({" ".join(keywords_list[:num_keywords])})[Title]']
            else:
                # 如果关键词太少，使用所有词（但限制数量）
                num_words = min(15, len(title_words))
                # 关键词之间用空格分隔，不用AND
                query_parts = [f'({" ".join(title_words[:num_words])})[Title]']
        
        if author:
            # 只取第一作者
            first_author = author.split(",")[0].strip() if "," in author else author.strip()
            if exact_match:
                # 精确匹配：使用引号
                query_parts.append(f'"{first_author}"[Author]')
            else:
                # 模糊匹配：不使用引号，允许部分匹配
                query_parts.append(f'{first_author}[Author]')
        
        if journal:
            if exact_match:
                # 精确匹配：使用引号
                query_parts.append(f'"{journal}"[Journal]')
            else:
                # 模糊匹配：使用关键词，关键词之间用空格分隔（不用AND）
                journal_words = journal.split()
                if len(journal_words) > 1:
                    # 多个词，用空格分隔，不用AND
                    query_parts.append(f'({" ".join(journal_words)})[Journal]')
                else:
                    # 单个词，直接使用
                    query_parts.append(f'{journal}[Journal]')
        
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
                    "sort": "relevance",  # 按最佳匹配排序
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
    
    async def search_by_author_journal(self, authors: Optional[List[str]] = None,
                                       author: Optional[str] = None,
                                       journal: Optional[str] = None,
                                       year: Optional[int] = None,
                                       volume: Optional[str] = None,
                                       issue: Optional[str] = None,
                                       exact_match: bool = True) -> List[str]:
        """通过作者、期刊、年份等字段搜索PMID列表（无标题情况）
        
        Args:
            authors: 作者列表（优先使用，多个作者用空格连接）
            author: 单个作者字符串（向后兼容，如果authors为空则使用）
            journal: 期刊名称
            year: 年份
            volume: 卷号（可选）
            issue: 期号（可选）
            exact_match: 是否使用精确匹配（默认True，使用引号；False时使用关键词匹配）
        """
        query_parts = []
        
        # 处理作者：优先使用authors列表，否则使用author字符串
        if authors and len(authors) > 0:
            # 使用全部作者，多个作者用空格连接
            authors_str = " ".join(authors)
            if exact_match:
                # 精确匹配：使用引号
                query_parts.append(f'"{authors_str}"[Author]')
            else:
                # 模糊匹配：多个作者用空格连接（等同于AND）
                query_parts.append(f'({authors_str})[Author]')
        elif author:
            # 向后兼容：如果传入的是单个作者字符串
            author_str = author.strip()
            if exact_match:
                # 精确匹配：使用引号
                query_parts.append(f'"{author_str}"[Author]')
            else:
                # 模糊匹配：直接使用
                query_parts.append(f'{author_str}[Author]')
        
        if journal:
            if exact_match:
                # 精确匹配：使用引号
                query_parts.append(f'"{journal}"[Journal]')
            else:
                # 模糊匹配：使用关键词，关键词之间用空格分隔（不用AND）
                journal_words = journal.split()
                if len(journal_words) > 1:
                    # 多个词，用空格分隔，不用AND
                    query_parts.append(f'({" ".join(journal_words)})[Journal]')
                else:
                    # 单个词，直接使用
                    query_parts.append(f'{journal}[Journal]')
        
        if year:
            query_parts.append(f'{year}[Publication Date]')
        
        if volume:
            query_parts.append(f'{volume}[Volume]')
        
        if issue:
            query_parts.append(f'{issue}[Issue]')
        
        # 至少需要作者或期刊之一
        if not query_parts:
            logger.info("  无标题搜索：至少需要作者或期刊信息")
            return []
        
        query = " AND ".join(query_parts)
        
        logger.info(f"  PubMed 无标题搜索查询: {query}")
        
        async with httpx.AsyncClient() as client:
            try:
                search_url = f"{PUBMED_BASE_URL}/esearch.fcgi"
                params = {
                    "db": "pubmed",
                    "term": query,
                    "retmode": "json",
                    "retmax": 20,  # 统一限制为20篇
                    "sort": "relevance",  # 按最佳匹配排序
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
                logger.error(f"无标题搜索出错: {str(e)}", exc_info=True)
        
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
    
    async def _evaluate_and_classify_articles(
        self, 
        articles: List[Dict[str, Any]], 
        keywords: Dict[str, Any],
        use_smart_matching: bool,
        similarity_service,
        exclude_doi_pmid: bool = False
    ) -> tuple:
        """评估文章并分类
        
        Returns:
            (high_confidence: List, candidates: List, discarded: List, doi_pmid_matched: List)
            - high_confidence: 相似度 > 0.9 的文章
            - candidates: 相似度 0.5-0.9 的文章（非DOI/PMID匹配）
            - discarded: 相似度 < 0.5 的文章
            - doi_pmid_matched: DOI/PMID匹配但相似度<0.9的文章
        """
        if not articles:
            return [], [], [], []
        
        # 准备候选文章的关键词列表
        candidate_keywords = []
        for article in articles:
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
            candidate_keywords.append(article_keywords)
        
        # 如果已通过DOI/PMID检索过，后续检索阶段排除DOI/PMID字段
        evaluation_keywords = keywords.copy()
        if exclude_doi_pmid:
            # 移除DOI/PMID字段，只关注其他字段
            evaluation_keywords = {k: v for k, v in keywords.items() if k not in ["doi", "pmid"]}
            logger.info(f"  已通过DOI/PMID检索过，后续检索阶段排除DOI/PMID字段，专注于其他字段匹配")
        
        # 批量计算相似度
        if use_smart_matching:
            scored_results = similarity_service.calculate_similarity_batch(
                evaluation_keywords, candidate_keywords, use_smart_matching=True, exclude_doi_pmid=exclude_doi_pmid
            )
        else:
            scored_results = similarity_service.calculate_similarity_batch(
                evaluation_keywords, candidate_keywords, use_smart_matching=False, exclude_doi_pmid=exclude_doi_pmid
            )
        
        # 分类文章
        high_confidence = []  # > 0.9
        candidates = []  # 0.5-0.9（非DOI/PMID匹配）
        discarded = []  # < 0.5
        doi_pmid_matched = []  # DOI/PMID匹配但相似度<0.9
        
        # 检查DOI/PMID匹配（如果已排除DOI/PMID，则不检查）
        has_doi_match = bool(keywords.get("doi")) and not exclude_doi_pmid
        has_pmid_match = bool(keywords.get("pmid")) and not exclude_doi_pmid
        
        for similarity, article_keywords in scored_results:
            # 找到对应的原始文章对象
            article = next(
                (a for a in articles if a.get("pmid") == article_keywords.get("pmid")),
                None
            )
            if not article:
                continue
            
            # 检查是否是DOI/PMID匹配（如果已排除DOI/PMID，则不会匹配）
            is_doi_pmid_match = False
            match_type = None  # "doi_match" 或 "pmid_match"
            
            # 首先检查文章是否已经有匹配类型标记（说明是通过DOI/PMID检索到的）
            if article.get("_match_type") in ["doi_match", "pmid_match"]:
                is_doi_pmid_match = True
                match_type = article.get("_match_type")
                logger.info(f"  文章已有匹配类型标记: {match_type}, PMID={article.get('pmid')}")
            elif not exclude_doi_pmid:
                # 如果没有匹配类型标记，则通过比较DOI/PMID来判断
                if has_doi_match and article_keywords.get("doi"):
                    if keywords.get("doi").lower().strip() == article_keywords.get("doi").lower().strip():
                        is_doi_pmid_match = True
                        match_type = "doi_match"
                if has_pmid_match and article_keywords.get("pmid"):
                    if str(keywords.get("pmid")).strip() == str(article_keywords.get("pmid")).strip():
                        is_doi_pmid_match = True
                        match_type = "pmid_match"
            
            # 在文章对象中添加匹配类型标记（如果还没有）
            if match_type and not article.get("_match_type"):
                article["_match_type"] = match_type
            
            if similarity > 0.9:
                # 即使相似度>0.9，如果是DOI/PMID匹配的，也要确保标记正确
                if is_doi_pmid_match and not article.get("_match_type"):
                    article["_match_type"] = match_type
                high_confidence.append((similarity, article))
                match_type_info = f" ({match_type})" if match_type else ""
                logger.info(f"  高置信度文章 (相似度={similarity:.4f}{match_type_info}): PMID={article.get('pmid')}")
            elif similarity >= 0.5:
                if is_doi_pmid_match:
                    # DOI/PMID匹配但相似度<0.9，加入特殊列表
                    doi_pmid_matched.append((similarity, article))
                    logger.info(f"  DOI/PMID匹配文章 (相似度={similarity:.4f}): PMID={article.get('pmid')}")
                else:
                    candidates.append((similarity, article))
                    logger.info(f"  候选文章 (相似度={similarity:.4f}): PMID={article.get('pmid')}")
            else:
                # 即使相似度<0.5，只要DOI/PMID匹配，也要加入特殊列表
                if is_doi_pmid_match:
                    doi_pmid_matched.append((similarity, article))
                    logger.info(f"  DOI/PMID匹配文章（相似度较低={similarity:.4f}，但DOI/PMID匹配）: PMID={article.get('pmid')}")
                else:
                    discarded.append((similarity, article))
                    logger.info(f"  丢弃文章 (相似度={similarity:.4f}): PMID={article.get('pmid')}")
        
        return high_confidence, candidates, discarded, doi_pmid_matched
    
    async def search_articles(self, keywords: Dict[str, Any], use_smart_matching: bool = False) -> List[Dict[str, Any]]:
        """根据关键词搜索文章，按优先级顺序，使用优化的检索策略
        
        Args:
            keywords: 检索关键词
            use_smart_matching: 是否使用大模型智能匹配（启用时会在每个优先级检索后立即评估）
        """
        logger.info("*" * 80)
        logger.info("开始 PubMed 检索（优化策略）")
        logger.info(f"检索关键词: {keywords}")
        logger.info(f"智能匹配: {'启用' if use_smart_matching else '禁用'}")
        
        # 导入相似度服务（延迟导入避免循环依赖）
        from app.services.similarity_service import SimilarityService
        similarity_service = SimilarityService()
        
        seen_pmids = set()
        candidate_list = []  # 存储相似度 0.5-0.9 的候选文章
        doi_pmid_matched_articles = []  # 存储DOI/PMID匹配但相似度<0.9的文章
        has_doi_pmid_searched = False  # 标记是否已经通过DOI/PMID检索过
        
        # 优先级0: PMID直接搜索（最可靠）
        if keywords.get("pmid"):
            has_doi_pmid_searched = True  # 标记已通过PMID检索
            pmid = str(keywords["pmid"]).strip()
            logger.info(f"[优先级0] 使用 PMID 直接检索: {pmid}")
            article = await self.fetch_article_details(pmid)
            if article:
                article["pmid"] = pmid
                # 添加PMID匹配类型标记
                article["_match_type"] = "pmid_match"
                seen_pmids.add(pmid)
                logger.info(f"  直接找到文章: {article.get('title', 'N/A')[:80]}...")
                
                # 立即评估（排除PMID字段，只看其他关键词的相似度）
                if use_smart_matching:
                    # 排除PMID字段来评估相似度
                    high_conf, cands, _, doi_pmid = await self._evaluate_and_classify_articles(
                        [article], keywords, use_smart_matching, similarity_service, exclude_doi_pmid=True
                    )
                    if high_conf:
                        # 排除PMID后，其他关键词相似度>0.9，直接返回
                        high_conf_article = high_conf[0][1]
                        logger.info(f"  排除PMID后，其他关键词相似度={high_conf[0][0]:.4f}>0.9，直接返回")
                        return [high_conf_article]
                    elif doi_pmid:
                        # 排除PMID后，其他关键词相似度<0.9，继续关键词检索
                        # 将PMID匹配的文章加入特殊列表
                        doi_pmid_matched_articles.extend(doi_pmid)
                        logger.info(f"  排除PMID后，其他关键词相似度<0.9，继续关键词检索。PMID匹配文章已加入列表")
                    elif cands:
                        # 这种情况不应该出现（因为文章是PMID匹配的）
                        # 但为了安全，也加入PMID匹配列表
                        doi_pmid_matched_articles.extend([(cands[0][0], article)])
                        logger.info(f"  排除PMID后，其他关键词相似度<0.9，继续关键词检索")
                    # 如果相似度<0.5，继续检索（虽然不太可能）
                else:
                    # 传统方法：PMID匹配直接返回
                    logger.info(f"PubMed 检索完成，共找到 1 篇文章")
                    return [article]
            else:
                logger.info("  未找到对应的文章")
        
        # 优先级1: DOI搜索
        doi_article = None
        if keywords.get("doi"):
            has_doi_pmid_searched = True  # 标记已通过DOI检索
            logger.info(f"[优先级1] 使用 DOI 检索: {keywords['doi']}")
            pmid = await self.search_by_doi(keywords["doi"])
            if pmid and pmid not in seen_pmids:
                logger.info(f"  找到 PMID: {pmid}")
                article = await self.fetch_article_details(pmid)
                if article:
                    article["pmid"] = pmid
                    # 添加DOI匹配类型标记
                    article["_match_type"] = "doi_match"
                    doi_article = article
                    seen_pmids.add(pmid)
                    logger.info(f"  检索到文章: {article.get('title', 'N/A')[:80]}...")
                    
                    # 立即评估（排除DOI字段，只看其他关键词的相似度）
                    if use_smart_matching:
                        # 排除DOI/PMID字段来评估相似度
                        high_conf, cands, _, doi_pmid = await self._evaluate_and_classify_articles(
                            [article], keywords, use_smart_matching, similarity_service, exclude_doi_pmid=True
                        )
                        if high_conf:
                            # 排除DOI后，其他关键词相似度>0.9，直接返回
                            high_conf_article = high_conf[0][1]
                            logger.info(f"  排除DOI后，其他关键词相似度={high_conf[0][0]:.4f}>0.9，直接返回")
                            return [high_conf_article]
                        elif doi_pmid:
                            # 排除DOI后，其他关键词相似度<0.9，继续关键词检索
                            # 将DOI匹配的文章加入特殊列表
                            doi_pmid_matched_articles.extend(doi_pmid)
                            logger.info(f"  排除DOI后，其他关键词相似度<0.9，继续关键词检索。DOI匹配文章已加入列表")
                        elif cands:
                            # 这种情况不应该出现（因为文章是DOI匹配的）
                            # 但为了安全，也加入DOI匹配列表
                            doi_pmid_matched_articles.extend([(cands[0][0], article)])
                            logger.info(f"  排除DOI后，其他关键词相似度<0.9，继续关键词检索")
                    else:
                        # 传统方法：如果只有DOI且无其他字段，直接返回
                        if not (keywords.get("title") or keywords.get("authors") or keywords.get("journal")):
                            logger.info(f"PubMed 检索完成，仅通过DOI找到文章，直接返回")
                            return [article]
            else:
                logger.info("  未找到匹配的 PMID")
        
        # 提取关键词字段
        title = keywords.get("title")
        first_author = None
        if keywords.get("authors"):
            first_author = keywords["authors"][0] if isinstance(keywords["authors"], list) else keywords["authors"]
        journal = keywords.get("journal")
        year = keywords.get("year")
        volume = keywords.get("volume")
        issue = keywords.get("issue")
        
        # 优先级1.5: 无标题情况下的搜索（在优先级2之前处理）
        if not title:
            logger.info(f"[优先级1.5] 无标题情况，使用作者+期刊+年份等字段搜索（模糊匹配）")
            
            # 获取全部作者列表
            all_authors = None
            if keywords.get("authors"):
                if isinstance(keywords["authors"], list):
                    all_authors = keywords["authors"]
                else:
                    all_authors = [keywords["authors"]]
            
            # 至少需要作者或期刊之一才能搜索
            if all_authors or journal:
                # 定义无标题模糊匹配策略（按可靠性从高到低）
                fuzzy_no_title_strategies = [
                    ("作者+期刊+年份+卷号+期号", all_authors, journal, year, volume, issue),
                    ("作者+期刊+年份+卷号", all_authors, journal, year, volume, None),
                    ("作者+期刊+年份", all_authors, journal, year, None, None),
                    ("作者+期刊", all_authors, journal, None, None, None),
                    ("作者+年份", all_authors, None, year, None, None),
                    ("期刊+年份", None, journal, year, None, None),
                    ("作者", all_authors, None, None, None, None),
                    ("期刊", None, journal, None, None, None),
                ]
                
                for strategy_name, authors_list, j, y, v, i in fuzzy_no_title_strategies:
                    # 跳过无效策略（缺少必要字段）
                    if strategy_name == "作者+期刊+年份+卷号+期号" and not (authors_list and j and y and v and i):
                        continue
                    if strategy_name == "作者+期刊+年份+卷号" and not (authors_list and j and y and v):
                        continue
                    if strategy_name == "作者+期刊+年份" and not (authors_list and j and y):
                        continue
                    if strategy_name == "作者+期刊" and not (authors_list and j):
                        continue
                    if strategy_name == "作者+年份" and not (authors_list and y):
                        continue
                    if strategy_name == "期刊+年份" and not (j and y):
                        continue
                    if strategy_name == "作者" and not authors_list:
                        continue
                    if strategy_name == "期刊" and not j:
                        continue
                    
                    logger.info(f"  策略: {strategy_name}")
                    pmids = await self.search_by_author_journal(
                        authors=authors_list, journal=j, year=y, volume=v, issue=i, exact_match=False
                    )
                    logger.info(f"    找到 {len(pmids)} 个 PMID")
                    
                    batch_articles = []
                    for pmid in pmids:
                        if pmid not in seen_pmids:
                            article = await self.fetch_article_details(pmid)
                            if article:
                                article["pmid"] = pmid
                                batch_articles.append(article)
                                seen_pmids.add(pmid)
                                logger.info(f"    检索到文章 [{pmid}]: {article.get('title', 'N/A')[:60]}...")
                    
                    # 立即评估这批文章（如果已通过DOI/PMID检索，排除DOI/PMID字段）
                    if batch_articles:
                        high_conf, cands, discarded, doi_pmid = await self._evaluate_and_classify_articles(
                            batch_articles, keywords, use_smart_matching, similarity_service,
                            exclude_doi_pmid=has_doi_pmid_searched
                        )
                        
                        # 高置信度：直接返回
                        if high_conf:
                            logger.info(f"  找到高置信度匹配（相似度={high_conf[0][0]:.4f}），直接返回")
                            return [high_conf[0][1]]
                        
                        # DOI/PMID匹配但相似度<0.9：加入特殊列表
                        if doi_pmid:
                            doi_pmid_matched_articles.extend(doi_pmid)
                            logger.info(f"  加入 {len(doi_pmid)} 篇DOI/PMID匹配文章到特殊列表")
                        
                        # 候选文章：加入候选列表
                        if cands:
                            candidate_list.extend(cands)
                            logger.info(f"  加入 {len(cands)} 篇候选文章到候选列表")
                        
                        # 丢弃的文章：不处理，继续下一策略
                        if discarded:
                            logger.info(f"  丢弃 {len(discarded)} 篇相似度<0.5的文章")
                        
                        # 如果找到候选文章，继续尝试更精确的策略（不break）
                        # 只有在找到高置信度时才break
            else:
                logger.info("  无标题且缺少作者和期刊信息，无法进行搜索")
        
        # 优先级2: 有标题情况下的模糊匹配（去掉精确匹配）
        if title:
            logger.info(f"[优先级2] 有标题情况，使用模糊匹配")
            
            # 提取标题关键词
            title_words = title.split()
            stop_words = {'the', 'a', 'an', 'and', 'or', 'for', 'of', 'in', 'on', 'at', 'to', 'by', 'with', 'is', 'are', 'was', 'were', 'from'}
            keywords_list = [w for w in title_words if w.lower() not in stop_words and len(w) > 2]
            
            # 如果去除停用词后关键词不足，使用所有词（但限制数量）
            if len(keywords_list) >= 3:
                num_keywords = min(15, len(keywords_list))
                key_title = " ".join(keywords_list[:num_keywords])
                logger.info(f"  使用关键词: {key_title[:80]}...")
            elif len(title_words) >= 3:
                # 如果关键词太少，使用所有词（但限制数量）
                num_words = min(15, len(title_words))
                key_title = " ".join(title_words[:num_words])
                logger.info(f"  关键词不足，使用所有词: {key_title[:80]}...")
            else:
                # 标题太短，使用所有词
                num_words = min(15, len(title_words))
                key_title = " ".join(title_words[:num_words]) if title_words else None
                if key_title:
                    logger.info(f"  标题较短，使用所有词: {key_title[:80]}...")
                else:
                    logger.info("  标题为空，跳过模糊匹配")
            
            if key_title:
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
                    
                    batch_articles = []
                    for pmid in pmids:
                        if pmid not in seen_pmids:
                            article = await self.fetch_article_details(pmid)
                            if article:
                                article["pmid"] = pmid
                                batch_articles.append(article)
                                seen_pmids.add(pmid)
                                logger.info(f"    检索到文章 [{pmid}]: {article.get('title', 'N/A')[:60]}...")
                    
                    # 立即评估这批文章
                    if batch_articles:
                        high_conf, cands, discarded, _ = await self._evaluate_and_classify_articles(
                            batch_articles, keywords, use_smart_matching, similarity_service
                        )
                        
                        # 高置信度：直接返回
                        if high_conf:
                            logger.info(f"  找到高置信度匹配（相似度={high_conf[0][0]:.4f}），直接返回")
                            return [high_conf[0][1]]
                        
                        # 候选文章：加入候选列表
                        if cands:
                            candidate_list.extend(cands)
                            logger.info(f"  加入 {len(cands)} 篇候选文章到候选列表")
                        
                        # 丢弃的文章：不处理，继续下一策略
                        if discarded:
                            logger.info(f"  丢弃 {len(discarded)} 篇相似度<0.5的文章")
                        
                        # 如果找到候选文章，继续尝试更精确的策略
        
        # 所有优先级检索完毕，处理候选列表
        logger.info(f"\n所有优先级检索完毕，候选列表中有 {len(candidate_list)} 篇文章")
        logger.info(f"DOI/PMID匹配列表中有 {len(doi_pmid_matched_articles)} 篇文章")
        
        # 如果候选列表为空，返回空结果
        if not candidate_list and not doi_pmid_matched_articles:
            logger.info(f"PubMed 检索完成，未找到匹配文章")
            return []
        
        # 如果只有DOI/PMID匹配的文章（没有其他候选文章），直接返回
        if not candidate_list and doi_pmid_matched_articles:
            logger.info(f"PubMed 检索完成，只有DOI/PMID匹配的文章，返回 {len(doi_pmid_matched_articles)} 篇")
            result_articles = []
            for score, article in doi_pmid_matched_articles:
                article["_similarity_score"] = score
                if "_match_type" not in article:
                    if keywords.get("doi") and article.get("doi"):
                        if keywords.get("doi").lower().strip() == article.get("doi").lower().strip():
                            article["_match_type"] = "doi_match"
                    elif keywords.get("pmid") and article.get("pmid"):
                        if str(keywords.get("pmid")).strip() == str(article.get("pmid")).strip():
                            article["_match_type"] = "pmid_match"
                result_articles.append(article)
            return result_articles
        
        # 如果候选列表只有一篇文章且没有DOI/PMID匹配的文章，直接返回
        if len(candidate_list) == 1 and not doi_pmid_matched_articles:
            logger.info(f"PubMed 检索完成，找到唯一候选文章")
            return [candidate_list[0][1]]
        
        # 如果候选列表有多篇文章，使用大模型最终评估
        if len(candidate_list) > 1 or (candidate_list and doi_pmid_matched_articles):
            logger.info(f"候选列表中有多篇文章，使用大模型最终评估")
            
            # 合并所有候选文章（去重）
            all_candidates = []
            seen_candidate_pmids = set()
            
            # 先添加DOI/PMID匹配的文章（优先级更高）
            for score, article in doi_pmid_matched_articles:
                if article.get("pmid") not in seen_candidate_pmids:
                    all_candidates.append((score, article))
                    seen_candidate_pmids.add(article.get("pmid"))
            
            # 再添加其他候选文章
            for score, article in candidate_list:
                if article.get("pmid") not in seen_candidate_pmids:
                    all_candidates.append((score, article))
                    seen_candidate_pmids.add(article.get("pmid"))
            
            # 如果启用大模型，使用大模型最终评估
            if use_smart_matching and len(all_candidates) > 1:
                logger.info(f"使用大模型对 {len(all_candidates)} 篇候选文章进行最终评估")
                candidate_articles = [article for _, article in all_candidates]
                candidate_keywords = []
                for article in candidate_articles:
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
                    candidate_keywords.append(article_keywords)
                
                # 最终评估：使用更详细的提示词
                if use_smart_matching:
                    from app.services.llm_service import LLMService
                    llm_service = LLMService()
                    final_scored = llm_service.evaluate_similarity_with_llm(
                        keywords, candidate_keywords, is_final_evaluation=True
                    )
                else:
                    final_scored = similarity_service.calculate_similarity_batch(
                        keywords, candidate_keywords, use_smart_matching=False
                    )
                
                # 按相似度排序
                final_scored.sort(key=lambda x: x[0], reverse=True)
                
                # 构建相似度到文章对象的映射（处理相同分数的情况）
                scored_articles = []
                for score, article_keywords in final_scored:
                    # 找到对应的原始文章对象
                    article = next(
                        (a for a in candidate_articles if a.get("pmid") == article_keywords.get("pmid")),
                        None
                    )
                    if article:
                        scored_articles.append((score, article))
                
                # 检查是否有匹配的文章
                # 如果最高相似度低于0.3，认为大模型判断没有匹配的文章
                NO_MATCH_THRESHOLD = 0.3
                result_articles = []
                best_score = 0.0
                best_article = None
                
                if scored_articles:
                    best_score, best_article = scored_articles[0]
                    
                    # 如果最高相似度低于阈值，但如果有DOI/PMID匹配的文章，仍然返回
                    if best_score < NO_MATCH_THRESHOLD:
                        logger.info(f"  最终评估：最高相似度={best_score:.4f} < {NO_MATCH_THRESHOLD}，大模型判断没有匹配的文章")
                        if doi_pmid_matched_articles:
                            logger.info(f"  但有DOI/PMID匹配的文章，仍然返回这些文章供用户选择")
                            # 只返回DOI/PMID匹配的文章
                            for score, article in doi_pmid_matched_articles:
                                article["_similarity_score"] = score
                                if "_match_type" not in article:
                                    if keywords.get("doi") and article.get("doi"):
                                        if keywords.get("doi").lower().strip() == article.get("doi").lower().strip():
                                            article["_match_type"] = "doi_match"
                                    elif keywords.get("pmid") and article.get("pmid"):
                                        if str(keywords.get("pmid")).strip() == str(article.get("pmid")).strip():
                                            article["_match_type"] = "pmid_match"
                                result_articles.append(article)
                            logger.info(f"PubMed 检索完成，返回 {len(result_articles)} 篇DOI/PMID匹配文章")
                            return result_articles
                        else:
                            logger.info(f"  所有候选文章的相似度都较低，可能都不是同一篇文章")
                            # 返回空列表，表示未找到匹配
                            logger.info(f"PubMed 检索完成，未找到匹配文章（最终评估）")
                            return []
                
                # 添加最可能的文章（关键词匹配的最优文章）
                if best_article:
                    # 在文章对象中添加相似度信息（临时字段）
                    best_article["_similarity_score"] = best_score
                    result_articles.append(best_article)
                    logger.info(f"  关键词匹配的最优文章: PMID={best_article.get('pmid')}, 相似度={best_score:.4f}")
                
                # 添加所有DOI/PMID匹配的文章（确保与关键词匹配的文章不同）
                seen_result_pmids = {best_article.get("pmid")} if best_article else set()
                for score, article in doi_pmid_matched_articles:
                    article_pmid = article.get("pmid")
                    if article_pmid not in seen_result_pmids:
                        # 在文章对象中添加相似度信息和匹配类型
                        article["_similarity_score"] = score
                        if "_match_type" not in article:
                            # 如果没有匹配类型，根据DOI/PMID判断
                            if keywords.get("doi") and article.get("doi"):
                                if keywords.get("doi").lower().strip() == article.get("doi").lower().strip():
                                    article["_match_type"] = "doi_match"
                            elif keywords.get("pmid") and article.get("pmid"):
                                if str(keywords.get("pmid")).strip() == str(article.get("pmid")).strip():
                                    article["_match_type"] = "pmid_match"
                        result_articles.append(article)
                        seen_result_pmids.add(article_pmid)
                        match_type_str = article.get("_match_type", "DOI/PMID匹配")
                        logger.info(f"  {match_type_str}文章（相似度={score:.4f}）: PMID={article_pmid}")
                
                logger.info(f"PubMed 检索完成，返回 {len(result_articles)} 篇文章供用户选择")
                return result_articles
            else:
                # 不使用大模型或只有一篇文章，直接返回排序后的结果
                all_candidates.sort(key=lambda x: x[0], reverse=True)
                result_articles = []
                for score, article in all_candidates:
                    article["_similarity_score"] = score
                    # 确保DOI/PMID匹配的文章有匹配类型标记
                    if "_match_type" not in article:
                        if keywords.get("doi") and article.get("doi"):
                            if keywords.get("doi").lower().strip() == article.get("doi").lower().strip():
                                article["_match_type"] = "doi_match"
                        elif keywords.get("pmid") and article.get("pmid"):
                            if str(keywords.get("pmid")).strip() == str(article.get("pmid")).strip():
                                article["_match_type"] = "pmid_match"
                    result_articles.append(article)
                logger.info(f"PubMed 检索完成，返回 {len(result_articles)} 篇文章")
                return result_articles
        
        # 如果只有候选列表中的文章，也要检查是否有DOI/PMID匹配的文章
        if doi_pmid_matched_articles:
            # 合并候选列表和DOI/PMID匹配列表
            all_articles = []
            seen_pmids_result = set()
            
            # 先添加DOI/PMID匹配的文章（优先级更高）
            for score, article in doi_pmid_matched_articles:
                if article.get("pmid") not in seen_pmids_result:
                    article["_similarity_score"] = score
                    if "_match_type" not in article:
                        if keywords.get("doi") and article.get("doi"):
                            if keywords.get("doi").lower().strip() == article.get("doi").lower().strip():
                                article["_match_type"] = "doi_match"
                        elif keywords.get("pmid") and article.get("pmid"):
                            if str(keywords.get("pmid")).strip() == str(article.get("pmid")).strip():
                                article["_match_type"] = "pmid_match"
                    all_articles.append(article)
                    seen_pmids_result.add(article.get("pmid"))
            
            # 再添加其他候选文章
            candidate_list.sort(key=lambda x: x[0], reverse=True)
            for score, article in candidate_list:
                if article.get("pmid") not in seen_pmids_result:
                    article["_similarity_score"] = score
                    all_articles.append(article)
                    seen_pmids_result.add(article.get("pmid"))
            
            logger.info(f"PubMed 检索完成，返回 {len(all_articles)} 篇文章（包含DOI/PMID匹配）")
            return all_articles
        else:
            # 只有候选列表中的文章
            candidate_list.sort(key=lambda x: x[0], reverse=True)
            result_articles = []
            for score, article in candidate_list:
                article["_similarity_score"] = score
                result_articles.append(article)
            logger.info(f"PubMed 检索完成，返回 {len(result_articles)} 篇文章")
            return result_articles

