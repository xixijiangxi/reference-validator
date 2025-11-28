from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ReferenceKeyword(BaseModel):
    """参考文献关键词"""
    title: Optional[str] = None
    authors: Optional[List[str]] = None
    journal: Optional[str] = None
    year: Optional[int] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    pages: Optional[str] = None
    pmid: Optional[str] = None
    doi: Optional[str] = None


class PubMedArticle(BaseModel):
    """PubMed文章信息"""
    pmid: Optional[str] = None
    title: Optional[str] = None
    authors: Optional[List[str]] = None
    journal: Optional[str] = None
    year: Optional[int] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    pages: Optional[str] = None
    doi: Optional[str] = None
    abstract: Optional[str] = None
    keywords: ReferenceKeyword = Field(default_factory=ReferenceKeyword)
    similarity_score: float = 0.0
    differences: Dict[str, Any] = Field(default_factory=dict)
    match_type: Optional[str] = None  # "doi_match" 或 "pmid_match"，表示通过DOI或PMID匹配到的文章


class ReferenceItem(BaseModel):
    """单条参考文献"""
    id: str
    original_text: str
    format_type: Optional[str] = None
    extracted_keywords: ReferenceKeyword = Field(default_factory=ReferenceKeyword)
    matched_articles: List[PubMedArticle] = Field(default_factory=list)
    status: str = "pending"  # pending, matched, not_found, completed


class ReferenceSplitRequest(BaseModel):
    """参考文献拆分请求"""
    text: str


class ReferenceSplitResponse(BaseModel):
    """参考文献拆分响应"""
    references: List[ReferenceItem]


class ReferenceProcessRequest(BaseModel):
    """参考文献处理请求"""
    reference_id: str
    action: str  # complete, replace, delete
    article_data: Optional[Dict[str, Any]] = None


class ReferenceFormatRequest(BaseModel):
    """参考文献格式转换请求"""
    references: List[Dict[str, Any]]
    target_format: str  # apa, mla, ama, nlm, gb2015, numeric, author_year

