from typing import Dict, Any, List, Optional
from difflib import SequenceMatcher
import logging

logger = logging.getLogger(__name__)


class SimilarityService:
    """相似度计算服务"""
    
    def __init__(self):
        # 关键词权重配置
        self.weights = {
            "doi": 0.3,
            "pmid": 0.25,
            "title": 0.2,
            "authors": 0.15,
            "journal": 0.05,
            "year": 0.03,
            "volume": 0.01,
            "issue": 0.01,
            "pages": 0.0
        }
    
    def calculate_similarity_batch(
        self, 
        original: Dict[str, Any], 
        candidates: List[Dict[str, Any]],
        use_smart_matching: bool = False,
        exclude_doi_pmid: bool = False
    ) -> List[tuple]:
        """批量计算相似度，支持传统方法和智能匹配
        
        Args:
            original: 原始参考文献的关键词
            candidates: 候选文章列表
            use_smart_matching: 是否使用大模型智能匹配
        
        Returns:
            List[tuple]: [(相似度分数, 文章信息), ...] 按相似度降序排序
        """
        if use_smart_matching:
            # 使用大模型评估
            try:
                from app.services.llm_service import LLMService
                llm_service = LLMService()
                # 默认是检索阶段评估（is_final_evaluation=False）
                return llm_service.evaluate_similarity_with_llm(original, candidates, is_final_evaluation=False, exclude_doi_pmid=exclude_doi_pmid)
            except Exception as e:
                logger.error(f"大模型评估失败，回退到传统方法: {str(e)}", exc_info=True)
                # 回退到传统方法
                return self._calculate_similarity_batch_traditional(original, candidates, exclude_doi_pmid=exclude_doi_pmid)
        else:
            # 使用传统方法
            return self._calculate_similarity_batch_traditional(original, candidates, exclude_doi_pmid=exclude_doi_pmid)
    
    def _calculate_similarity_batch_traditional(
        self, 
        original: Dict[str, Any], 
        candidates: List[Dict[str, Any]],
        exclude_doi_pmid: bool = False
    ) -> List[tuple]:
        """使用传统方法批量计算相似度"""
        scored_results = []
        for candidate in candidates:
            similarity = self.calculate_similarity(original, candidate, exclude_doi_pmid=exclude_doi_pmid)
            scored_results.append((similarity, candidate))
        
        # 按相似度降序排序
        scored_results.sort(key=lambda x: x[0], reverse=True)
        return scored_results
    
    def calculate_similarity(self, original: Dict[str, Any], matched: Dict[str, Any], exclude_doi_pmid: bool = False) -> float:
        """计算两个参考文献的相似度
        
        Args:
            original: 原始参考文献的关键词
            matched: 匹配文章的关键词
            exclude_doi_pmid: 是否排除DOI/PMID字段（用于后续检索阶段）
        """
        logger.info("+" * 80)
        logger.info("开始计算相似度")
        logger.info(f"原始关键词: {original}")
        logger.info(f"匹配文章关键词: {matched}")
        if exclude_doi_pmid:
            logger.info("  排除DOI/PMID字段，专注于其他字段匹配")
        
        total_score = 0.0
        total_weight = 0.0
        details = []
        
        # DOI完全匹配（但不直接返回，继续计算其他字段以检测冲突）
        if not exclude_doi_pmid:
            doi_matched = False
            if original.get("doi") and matched.get("doi"):
                if original["doi"].lower().strip() == matched["doi"].lower().strip():
                    doi_matched = True
                    total_score += 1.0 * self.weights["doi"]
                    total_weight += self.weights["doi"]
                    details.append(f"DOI完全匹配 (权重{self.weights['doi']}): 得分1.0")
                else:
                    # DOI不匹配，相似度降低
                    total_score += 0.0
                    total_weight += self.weights["doi"]
                    details.append(f"DOI不匹配: {original['doi']} != {matched['doi']}")
            
            # 如果DOI匹配且没有其他字段，直接返回100%
            if doi_matched and not (original.get("title") or original.get("authors") or original.get("journal")):
                logger.info(f"  [DOI] 完全匹配且无其他字段，相似度=100%")
                return 1.0
            
            # PMID完全匹配
            if original.get("pmid") and matched.get("pmid"):
                if str(original["pmid"]).strip() == str(matched["pmid"]).strip():
                    total_score += 1.0 * self.weights["pmid"]
                    total_weight += self.weights["pmid"]
                    details.append(f"PMID匹配 (权重{self.weights['pmid']}): 得分1.0")
                else:
                    total_weight += self.weights["pmid"]
                    details.append(f"PMID不匹配: {original['pmid']} != {matched['pmid']}")
        
        # 标题相似度
        if original.get("title") and matched.get("title"):
            title_sim = self._text_similarity(original["title"], matched["title"])
            total_score += title_sim * self.weights["title"]
            total_weight += self.weights["title"]
            details.append(f"标题相似度 (权重{self.weights['title']}): {title_sim:.2f}")
        
        # 作者相似度
        if original.get("authors") and matched.get("authors"):
            author_sim = self._authors_similarity(original["authors"], matched["authors"])
            total_score += author_sim * self.weights["authors"]
            total_weight += self.weights["authors"]
            details.append(f"作者相似度 (权重{self.weights['authors']}): {author_sim:.2f}")
        
        # 期刊相似度
        if original.get("journal") and matched.get("journal"):
            journal_sim = self._text_similarity(original["journal"], matched["journal"])
            total_score += journal_sim * self.weights["journal"]
            total_weight += self.weights["journal"]
            details.append(f"期刊相似度 (权重{self.weights['journal']}): {journal_sim:.2f}")
        
        # 年份匹配
        if original.get("year") and matched.get("year"):
            if original["year"] == matched["year"]:
                total_score += 1.0 * self.weights["year"]
                details.append(f"年份匹配 (权重{self.weights['year']}): {original['year']} == {matched['year']}")
            else:
                details.append(f"年份不匹配: {original['year']} != {matched['year']}")
            total_weight += self.weights["year"]
        
        # 卷号匹配
        if original.get("volume") and matched.get("volume"):
            if str(original["volume"]).strip() == str(matched["volume"]).strip():
                total_score += 1.0 * self.weights["volume"]
                details.append(f"卷号匹配 (权重{self.weights['volume']}): {original['volume']}")
            total_weight += self.weights["volume"]
        
        # 期号匹配
        if original.get("issue") and matched.get("issue"):
            if str(original["issue"]).strip() == str(matched["issue"]).strip():
                total_score += 1.0 * self.weights["issue"]
                details.append(f"期号匹配 (权重{self.weights['issue']}): {original['issue']}")
            total_weight += self.weights["issue"]
        
        if total_weight == 0:
            logger.info("  总权重为0，相似度=0.0")
            return 0.0
        
        final_similarity = total_score / total_weight
        logger.info(f"  相似度计算详情:")
        for detail in details:
            logger.info(f"    - {detail}")
        logger.info(f"  最终相似度: {final_similarity:.4f} (总得分={total_score:.4f}, 总权重={total_weight:.4f})")
        
        return final_similarity
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """计算两个文本的相似度"""
        if not text1 or not text2:
            return 0.0
        
        # 标准化文本
        text1 = text1.lower().strip()
        text2 = text2.lower().strip()
        
        if text1 == text2:
            return 1.0
        
        # 使用SequenceMatcher计算相似度
        return SequenceMatcher(None, text1, text2).ratio()
    
    def _authors_similarity(self, authors1: List[str], authors2: List[str]) -> float:
        """计算作者列表的相似度"""
        if not authors1 or not authors2:
            return 0.0
        
        # 标准化作者名称
        def normalize_author(author: str) -> str:
            return author.lower().strip().replace(",", "").replace(".", "")
        
        authors1_normalized = [normalize_author(a) for a in authors1]
        authors2_normalized = [normalize_author(a) for a in authors2]
        
        # 计算第一作者匹配
        if authors1_normalized and authors2_normalized:
            first_author_sim = self._text_similarity(
                authors1_normalized[0],
                authors2_normalized[0]
            )
            
            # 计算所有作者的匹配度
            matched = 0
            for a1 in authors1_normalized:
                for a2 in authors2_normalized:
                    if self._text_similarity(a1, a2) > 0.8:
                        matched += 1
                        break
            
            # 综合相似度
            avg_match = matched / max(len(authors1_normalized), len(authors2_normalized))
            return (first_author_sim * 0.5 + avg_match * 0.5)
        
        return 0.0
    
    def find_differences(self, original: Dict[str, Any], matched: Dict[str, Any]) -> Dict[str, Any]:
        """找出两个参考文献之间的差异"""
        differences = {}
        
        # 检查每个字段
        fields = ["title", "authors", "journal", "year", "volume", "issue", "pages", "pmid", "doi"]
        
        for field in fields:
            orig_val = original.get(field)
            match_val = matched.get(field)
            
            if orig_val is None and match_val is not None:
                differences[field] = {"type": "missing", "value": match_val}
            elif orig_val is not None and match_val is None:
                differences[field] = {"type": "extra", "value": orig_val}
            elif orig_val is not None and match_val is not None:
                # 比较值是否相同
                if field == "authors":
                    if not self._authors_match(orig_val, match_val):
                        differences[field] = {
                            "type": "different",
                            "original": orig_val,
                            "matched": match_val
                        }
                elif str(orig_val).strip().lower() != str(match_val).strip().lower():
                    differences[field] = {
                        "type": "different",
                        "original": orig_val,
                        "matched": match_val
                    }
        
        return differences
    
    def _authors_match(self, authors1: List[str], authors2: List[str]) -> bool:
        """检查两个作者列表是否匹配"""
        if not authors1 or not authors2:
            return False
        
        def normalize(author: str) -> str:
            return author.lower().strip().replace(",", "").replace(".", "")
        
        authors1_norm = [normalize(a) for a in authors1]
        authors2_norm = [normalize(a) for a in authors2]
        
        # 检查第一作者
        if authors1_norm[0] != authors2_norm[0]:
            return False
        
        # 检查是否有足够的共同作者
        common = 0
        for a1 in authors1_norm:
            if a1 in authors2_norm:
                common += 1
        
        return common >= min(len(authors1_norm), len(authors2_norm)) * 0.7

