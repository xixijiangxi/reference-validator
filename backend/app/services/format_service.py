from typing import List, Dict, Any


class FormatService:
    """参考文献格式化服务"""
    
    def format_apa(self, ref: Dict[str, Any]) -> str:
        """APA格式"""
        authors = ref.get("data", {}).get("authors", [])
        year = ref.get("data", {}).get("year")
        title = ref.get("data", {}).get("title", "")
        journal = ref.get("data", {}).get("journal", "")
        volume = ref.get("data", {}).get("volume", "")
        issue = ref.get("data", {}).get("issue", "")
        pages = ref.get("data", {}).get("pages", "")
        doi = ref.get("data", {}).get("doi", "")
        
        # 格式化作者
        author_str = ""
        if authors:
            if len(authors) == 1:
                author_str = authors[0]
            elif len(authors) == 2:
                author_str = f"{authors[0]} & {authors[1]}"
            else:
                author_str = f"{authors[0]}, et al."
        
        # 格式化期刊信息
        journal_info = journal
        if volume:
            journal_info += f", {volume}"
        if issue:
            journal_info += f"({issue})"
        if pages:
            journal_info += f", {pages}"
        
        # 构建引用
        parts = []
        if author_str:
            parts.append(f"{author_str}")
        if year:
            parts.append(f"({year})")
        if title:
            parts.append(title)
        if journal_info:
            parts.append(journal_info)
        if doi:
            parts.append(f"https://doi.org/{doi}")
        
        return ". ".join(parts) + "."
    
    def format_mla(self, ref: Dict[str, Any]) -> str:
        """MLA格式"""
        authors = ref.get("data", {}).get("authors", [])
        title = ref.get("data", {}).get("title", "")
        journal = ref.get("data", {}).get("journal", "")
        volume = ref.get("data", {}).get("volume", "")
        issue = ref.get("data", {}).get("issue", "")
        year = ref.get("data", {}).get("year")
        pages = ref.get("data", {}).get("pages", "")
        
        author_str = ", ".join(authors) if authors else ""
        journal_info = f'"{journal}"' if journal else ""
        
        parts = []
        if author_str:
            parts.append(f"{author_str}.")
        if title:
            parts.append(f'"{title}."')
        if journal_info:
            parts.append(journal_info)
        if volume:
            parts.append(f"vol. {volume}")
        if issue:
            parts.append(f"no. {issue}")
        if year:
            parts.append(str(year))
        if pages:
            parts.append(f"pp. {pages}")
        
        return ", ".join(parts) + "."
    
    def format_ama(self, ref: Dict[str, Any]) -> str:
        """AMA格式"""
        authors = ref.get("data", {}).get("authors", [])
        title = ref.get("data", {}).get("title", "")
        journal = ref.get("data", {}).get("journal", "")
        year = ref.get("data", {}).get("year")
        volume = ref.get("data", {}).get("volume", "")
        issue = ref.get("data", {}).get("issue", "")
        pages = ref.get("data", {}).get("pages", "")
        
        # AMA格式：作者. 标题. 期刊. 年份;卷(期):页码.
        author_str = ", ".join(authors[:6]) if authors else ""
        if len(authors) > 6:
            author_str += " et al"
        
        parts = []
        if author_str:
            parts.append(f"{author_str}.")
        if title:
            parts.append(title)
        if journal:
            parts.append(journal)
        if year:
            parts.append(str(year))
        if volume:
            vol_info = f";{volume}"
            if issue:
                vol_info += f"({issue})"
            parts.append(vol_info)
        if pages:
            parts.append(f":{pages}")
        
        return ". ".join(parts) + "."
    
    def format_nlm(self, ref: Dict[str, Any]) -> str:
        """NLM格式（不包含PMID，根据用户要求）"""
        authors = ref.get("data", {}).get("authors", [])
        title = ref.get("data", {}).get("title", "")
        journal = ref.get("data", {}).get("journal", "")
        year = ref.get("data", {}).get("year")
        volume = ref.get("data", {}).get("volume", "")
        issue = ref.get("data", {}).get("issue", "")
        pages = ref.get("data", {}).get("pages", "")
        
        author_str = ", ".join(authors[:6]) if authors else ""
        if len(authors) > 6:
            author_str += ", et al"
        
        parts = []
        if author_str:
            parts.append(f"{author_str}.")
        if title:
            parts.append(title)
        if journal:
            parts.append(journal)
        if year:
            parts.append(str(year))
        if volume:
            vol_info = f"{volume}"
            if issue:
                vol_info += f"({issue})"
            parts.append(vol_info)
        if pages:
            parts.append(f":{pages}")
        # 根据用户要求，一般格式中不包含PMID
        
        return ". ".join(parts) + "."
    
    def format_gb2015(self, ref: Dict[str, Any]) -> str:
        """国标2015格式"""
        authors = ref.get("data", {}).get("authors", [])
        title = ref.get("data", {}).get("title", "")
        journal = ref.get("data", {}).get("journal", "")
        year = ref.get("data", {}).get("year")
        volume = ref.get("data", {}).get("volume", "")
        issue = ref.get("data", {}).get("issue", "")
        pages = ref.get("data", {}).get("pages", "")
        
        # 国标格式：作者. 题名[J]. 刊名, 年份, 卷(期): 页码.
        author_str = ", ".join(authors) if authors else ""
        
        parts = []
        if author_str:
            parts.append(f"{author_str}.")
        if title:
            parts.append(f"{title}[J].")
        if journal:
            parts.append(journal)
        if year:
            parts.append(str(year))
        if volume:
            vol_info = f"{volume}"
            if issue:
                vol_info += f"({issue})"
            parts.append(vol_info)
        if pages:
            parts.append(f":{pages}")
        
        return ", ".join(parts) + "."
    
    def format_numeric(self, ref: Dict[str, Any], index: int) -> str:
        """顺序编码制格式"""
        authors = ref.get("data", {}).get("authors", [])
        title = ref.get("data", {}).get("title", "")
        journal = ref.get("data", {}).get("journal", "")
        year = ref.get("data", {}).get("year")
        volume = ref.get("data", {}).get("volume", "")
        issue = ref.get("data", {}).get("issue", "")
        pages = ref.get("data", {}).get("pages", "")
        
        author_str = ", ".join(authors) if authors else ""
        
        parts = [f"[{index}]"]
        if author_str:
            parts.append(f"{author_str}.")
        if title:
            parts.append(title)
        if journal:
            parts.append(journal)
        if year:
            parts.append(str(year))
        if volume:
            vol_info = f"{volume}"
            if issue:
                vol_info += f"({issue})"
            parts.append(vol_info)
        if pages:
            parts.append(f":{pages}")
        
        return " ".join(parts) + "."
    
    def format_author_year(self, ref: Dict[str, Any]) -> str:
        """著者出版年制格式"""
        authors = ref.get("data", {}).get("authors", [])
        year = ref.get("data", {}).get("year")
        title = ref.get("data", {}).get("title", "")
        journal = ref.get("data", {}).get("journal", "")
        volume = ref.get("data", {}).get("volume", "")
        issue = ref.get("data", {}).get("issue", "")
        pages = ref.get("data", {}).get("pages", "")
        
        author_str = ", ".join(authors) if authors else ""
        
        parts = []
        if author_str and year:
            parts.append(f"{author_str}({year})")
        elif author_str:
            parts.append(author_str)
        if title:
            parts.append(title)
        if journal:
            parts.append(journal)
        if volume:
            vol_info = f"{volume}"
            if issue:
                vol_info += f"({issue})"
            parts.append(vol_info)
        if pages:
            parts.append(f":{pages}")
        
        return ". ".join(parts) + "."
    
    def format_references(self, references: List[Dict[str, Any]], target_format: str) -> str:
        """格式化参考文献列表"""
        formatted = []
        
        for idx, ref in enumerate(references, 1):
            if target_format == "apa":
                formatted.append(self.format_apa(ref))
            elif target_format == "mla":
                formatted.append(self.format_mla(ref))
            elif target_format == "ama":
                formatted.append(self.format_ama(ref))
            elif target_format == "nlm":
                formatted.append(self.format_nlm(ref))
            elif target_format == "gb2015":
                formatted.append(self.format_gb2015(ref))
            elif target_format == "numeric":
                formatted.append(self.format_numeric(ref, idx))
            elif target_format == "author_year":
                formatted.append(self.format_author_year(ref))
            else:
                # 原始格式
                formatted.append(ref.get("text", ""))
        
        return "\n".join(formatted)

