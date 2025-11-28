from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import uuid
import logging
from app.models import (
    ReferenceSplitRequest, ReferenceSplitResponse, ReferenceItem,
    ReferenceKeyword, PubMedArticle
)
from app.services.llm_service import LLMService
from app.services.pubmed_service import PubMedService
from app.services.similarity_service import SimilarityService
from app.services.format_service import FormatService

logger = logging.getLogger(__name__)

router = APIRouter()
llm_service = LLMService()
pubmed_service = PubMedService()
similarity_service = SimilarityService()
format_service = FormatService()


@router.post("/split", response_model=ReferenceSplitResponse)
async def split_references(request: ReferenceSplitRequest):
    """拆分参考文献列表"""
    logger.info("\n" + "="*100)
    logger.info("【API /split】收到参考文献拆分请求")
    logger.info(f"请求文本长度: {len(request.text)} 字符")
    
    try:
        # 使用LLM拆分参考文献
        split_results = llm_service.split_references(request.text)
        logger.info(f"拆分结果: 共 {len(split_results)} 条参考文献")
        
        references = []
        for idx, ref_data in enumerate(split_results):
            ref_id = ref_data.get("id", f"ref_{idx+1}")
            ref_text = ref_data.get("text", "")
            format_type = ref_data.get("format_type", "unknown")
            
            logger.info(f"\n处理第 {idx+1} 条参考文献: {ref_id}")
            
            # 提取关键词
            keywords_dict = llm_service.extract_keywords(ref_text)
            keywords = ReferenceKeyword(**keywords_dict)
            
            reference = ReferenceItem(
                id=ref_id,
                original_text=ref_text,
                format_type=format_type,
                extracted_keywords=keywords,
                status="pending"
            )
            references.append(reference)
        
        logger.info(f"\n【API /split】拆分完成，返回 {len(references)} 条参考文献")
        return ReferenceSplitResponse(references=references)
    except Exception as e:
        logger.error(f"【API /split】拆分失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"拆分参考文献失败: {str(e)}")


@router.post("/search/{reference_id}")
async def search_reference(reference_id: str, keywords: Dict[str, Any]):
    """搜索参考文献"""
    logger.info("\n" + "="*100)
    logger.info(f"【API /search】收到参考文献检索请求: {reference_id}")
    logger.info(f"输入关键词: {keywords}")
    
    # 提取智能匹配参数
    use_smart_matching = keywords.get("use_smart_matching", False)
    logger.info(f"智能匹配: {'启用' if use_smart_matching else '禁用'}")
    
    try:
        # 转换关键词格式（排除use_smart_matching）
        keywords_dict = {
            "title": keywords.get("title"),
            "authors": keywords.get("authors"),
            "journal": keywords.get("journal"),
            "year": keywords.get("year"),
            "volume": keywords.get("volume"),
            "issue": keywords.get("issue"),
            "pages": keywords.get("pages"),
            "pmid": keywords.get("pmid"),
            "doi": keywords.get("doi")
        }
        
        # 搜索文章
        articles = await pubmed_service.search_articles(keywords_dict, use_smart_matching=use_smart_matching)
        
        if not articles:
            logger.info(f"【API /search】未找到匹配文章: {reference_id}")
            return {
                "reference_id": reference_id,
                "matched_articles": [],
                "status": "not_found"
            }
        
        logger.info(f"【API /search】检索服务返回 {len(articles)} 篇文章（已内部评估和筛选）")
        
        # search_articles 已经在内部完成了评估和筛选，这里只需要构建响应对象
        # 使用文章中的相似度信息（如果存在），否则重新计算
        matched_articles = []
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
            
            # 使用文章中的相似度信息（如果存在），否则重新计算
            if "_similarity_score" in article:
                similarity = article["_similarity_score"]
                # 移除临时字段
                del article["_similarity_score"]
            else:
                similarity = similarity_service.calculate_similarity(keywords_dict, article_keywords)
            
            # 获取匹配类型（如果存在）
            match_type = article.get("_match_type")
            if match_type and "_match_type" in article:
                # 移除临时字段
                del article["_match_type"]
            
            differences = similarity_service.find_differences(keywords_dict, article_keywords)
            
            matched_article = PubMedArticle(
                pmid=article.get("pmid"),
                title=article.get("title"),
                authors=article.get("authors", []),
                journal=article.get("journal"),
                year=article.get("year"),
                volume=article.get("volume"),
                issue=article.get("issue"),
                pages=article.get("pages"),
                doi=article.get("doi"),
                abstract=article.get("abstract"),
                keywords=ReferenceKeyword(**article_keywords),
                similarity_score=similarity,
                differences=differences,
                match_type=match_type
            )
            matched_articles.append(matched_article)
            match_type_str = f" ({match_type})" if match_type else ""
            logger.info(f"  文章 PMID={article.get('pmid')}, 相似度={similarity:.4f}{match_type_str}")
        logger.info(f"\n相似度排序后，共 {len(matched_articles)} 篇匹配文章")
        for idx, art in enumerate(matched_articles, 1):
            match_type_info = f", 匹配类型={art.match_type}" if art.match_type else ""
            logger.info(f"  [{idx}] PMID={art.pmid}, 相似度={art.similarity_score:.4f}{match_type_info}, 标题={art.title[:60]}...")
        
        # 注意：不再截断结果，即使相似度100%也返回所有匹配的文章（包括DOI匹配的文章）
        # 这样用户可以看到所有可能的匹配结果并选择
        
        status = "matched" if matched_articles else "not_found"
        
        logger.info(f"【API /search】检索完成: {reference_id}, 状态={status}, 返回 {len(matched_articles)} 篇文章")
        return {
            "reference_id": reference_id,
            "matched_articles": [article.dict() for article in matched_articles],
            "status": status
        }
    except Exception as e:
        logger.error(f"【API /search】检索失败: {reference_id}, 错误: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"搜索参考文献失败: {str(e)}")


@router.post("/format")
async def format_references(request: Dict[str, Any]):
    """格式化参考文献"""
    references = request.get("references", [])
    target_format = request.get("target_format", "original")
    
    # 使用格式化服务
    formatted_text = format_service.format_references(references, target_format)
    
    return {
        "references": references,
        "format": target_format,
        "formatted_text": formatted_text
    }

