from typing import List, Dict, Any, Optional


class FormatService:
    """参考文献格式化服务"""
    
    def _format_author_apa(self, authors: List[str]) -> str:
        """格式化APA格式的作者"""
        if not authors:
            return ""
        if len(authors) == 1:
            return authors[0]
        elif len(authors) == 2:
            return f"{authors[0]}, {authors[1]}"
        else:
            return f"{authors[0]}, {authors[1]}, et al."
    
    def _format_author_mla(self, authors: List[str]) -> str:
        """格式化MLA格式的作者"""
        if not authors:
            return ""
        if len(authors) == 1:
            return authors[0]
        elif len(authors) == 2:
            return f"{authors[0]}, and {authors[1]}"
        else:
            return f"{authors[0]}, {', '.join(authors[1:-1])}, and {authors[-1]}"
    
    def _format_author_ama_nlm(self, authors: List[str]) -> str:
        """格式化AMA/NLM格式的作者（最多6个）"""
        if not authors:
            return ""
        if len(authors) <= 6:
            return ", ".join(authors)
        else:
            return ", ".join(authors[:6]) + " et al"
    
    def format_apa(self, ref: Dict[str, Any]) -> str:
        """APA格式: Smith J, Brown T. (2020). Title of article. Journal Name, 12(3): 123-130. doi:10.xxxx"""
        data = ref.get("data", {})
        authors = data.get("authors", [])
        year = data.get("year")
        title = data.get("title", "")
        journal = data.get("journal", "")
        volume = data.get("volume", "")
        issue = data.get("issue", "")
        pages = data.get("pages", "")
        doi = data.get("doi", "")
        
        # 格式化作者
        author_str = self._format_author_apa(authors)
        
        # 构建引用
        parts = []
        if author_str:
            parts.append(f"{author_str}.")
        if year:
            parts.append(f"({year}).")
        if title:
            parts.append(title)
        if journal:
            journal_part = journal
            if volume:
                journal_part += f", {volume}"
                if issue:
                    journal_part += f"({issue})"
                if pages:
                    journal_part += f": {pages}"
            parts.append(journal_part)
        if doi:
            # 确保DOI格式正确（去掉https://doi.org/前缀如果存在）
            doi_clean = doi.replace("https://doi.org/", "").replace("doi:", "").strip()
            parts.append(f"doi:{doi_clean}")
        
        result = " ".join(parts)
        if not result.endswith("."):
            result += "."
        return result
    
    def format_mla(self, ref: Dict[str, Any]) -> str:
        """MLA格式: Smith, John, and Tim Brown. "Article Title." Journal Name, vol. 12, no. 3, 2020, pp. 123-130."""
        data = ref.get("data", {})
        authors = data.get("authors", [])
        title = data.get("title", "")
        journal = data.get("journal", "")
        volume = data.get("volume", "")
        issue = data.get("issue", "")
        year = data.get("year")
        pages = data.get("pages", "")
        
        # 格式化作者
        author_str = self._format_author_mla(authors)
        
        parts = []
        if author_str:
            parts.append(f"{author_str}.")
        if title:
            parts.append(f'"{title}."')
        if journal:
            parts.append(journal)
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
        """AMA格式: Smith J, Brown T. Title of article. Journal Name. 2020;12(3):123-130. doi:10.xxxx"""
        data = ref.get("data", {})
        authors = data.get("authors", [])
        title = data.get("title", "")
        journal = data.get("journal", "")
        year = data.get("year")
        volume = data.get("volume", "")
        issue = data.get("issue", "")
        pages = data.get("pages", "")
        doi = data.get("doi", "")
        
        # 格式化作者
        author_str = self._format_author_ama_nlm(authors)
        
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
                if pages:
                    vol_info += f":{pages}"
                parts.append(vol_info)
        
        result = ". ".join(parts)
        if doi:
            doi_clean = doi.replace("https://doi.org/", "").replace("doi:", "").strip()
            result += f". doi:{doi_clean}"
        elif not result.endswith("."):
            result += "."
        return result
    
    def format_nlm(self, ref: Dict[str, Any]) -> str:
        """NLM格式: Smith J, Brown T. Title of article. J Clin Invest. 2020 Feb;130(2):123-130. doi:10.xxxx. PMID: 12345678."""
        data = ref.get("data", {})
        authors = data.get("authors", [])
        title = data.get("title", "")
        journal = data.get("journal", "")
        year = data.get("year")
        volume = data.get("volume", "")
        issue = data.get("issue", "")
        pages = data.get("pages", "")
        doi = data.get("doi", "")
        pmid = data.get("pmid", "")
        
        # 格式化作者
        author_str = self._format_author_ama_nlm(authors)
        
        # 月份映射（如果需要，可以从数据中获取，这里简化处理）
        month_map = {
            "01": "Jan", "02": "Feb", "03": "Mar", "04": "Apr",
            "05": "May", "06": "Jun", "07": "Jul", "08": "Aug",
            "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dec"
        }
        month = ""  # 如果数据中有月份信息，可以在这里处理
        
        parts = []
        if author_str:
            parts.append(f"{author_str}.")
        if title:
            parts.append(title)
        if journal:
            parts.append(journal)
        if year:
            year_part = str(year)
            if month:
                year_part += f" {month}"
            parts.append(year_part)
            if volume:
                vol_info = f";{volume}"
                if issue:
                    vol_info += f"({issue})"
                if pages:
                    vol_info += f":{pages}"
                parts.append(vol_info)
        
        result = ". ".join(parts)
        if doi:
            doi_clean = doi.replace("https://doi.org/", "").replace("doi:", "").strip()
            result += f". doi:{doi_clean}"
        if pmid:
            pmid_clean = pmid.replace("PMID:", "").replace("PMID", "").strip()
            result += f". PMID: {pmid_clean}"
        if not result.endswith("."):
            result += "."
        return result
    
    def format_gb2015(self, ref: Dict[str, Any], index: Optional[int] = None) -> str:
        """国标2015格式: [1] 张三, 李四. 文献题名[J]. 期刊名, 2020, 12(3):123-130. DOI:10.xxxx"""
        data = ref.get("data", {})
        authors = data.get("authors", [])
        title = data.get("title", "")
        journal = data.get("journal", "")
        year = data.get("year")
        volume = data.get("volume", "")
        issue = data.get("issue", "")
        pages = data.get("pages", "")
        doi = data.get("doi", "")
        
        # 类型标记，默认为J（期刊文章）
        ref_type = "J"
        
        parts = []
        if index is not None:
            parts.append(f"[{index}]")
        if authors:
            author_str = ", ".join(authors)
            parts.append(f"{author_str}.")
        if title:
            parts.append(f"{title}[{ref_type}].")
        if journal:
            parts.append(journal)
        if year:
            parts.append(str(year))
        if volume:
            vol_info = f"{volume}"
            if issue:
                vol_info += f"({issue})"
            if pages:
                vol_info += f":{pages}"
            parts.append(vol_info)
        
        result = ", ".join(parts)
        if doi:
            doi_clean = doi.replace("https://doi.org/", "").replace("DOI:", "").replace("doi:", "").strip()
            result += f". DOI:{doi_clean}"
        if not result.endswith("."):
            result += "."
        return result
    
    def format_numeric(self, ref: Dict[str, Any], index: int) -> str:
        """顺序编码制格式: 1.张三，李四. 标题[J]. 期刊, 2020, 12(3): 123-130."""
        data = ref.get("data", {})
        authors = data.get("authors", [])
        title = data.get("title", "")
        journal = data.get("journal", "")
        year = data.get("year")
        volume = data.get("volume", "")
        issue = data.get("issue", "")
        pages = data.get("pages", "")
        
        # 类型标记，默认为J（期刊文章）
        ref_type = "J"
        
        parts = [f"{index}."]
        if authors:
            author_str = "，".join(authors)  # 中文逗号
            parts.append(f"{author_str}.")
        if title:
            parts.append(f"{title}[{ref_type}].")
        if journal:
            parts.append(journal)
        if year:
            parts.append(str(year))
        if volume:
            vol_info = f"{volume}"
            if issue:
                vol_info += f"({issue})"
            if pages:
                vol_info += f": {pages}"
            parts.append(vol_info)
        
        result = ", ".join(parts)
        if not result.endswith("."):
            result += "."
        return result
    
    def format_author_year(self, ref: Dict[str, Any]) -> str:
        """著者出版年制格式: 张三, 李四. 2020. 标题[J]. 期刊, 12(3): 123-130."""
        data = ref.get("data", {})
        authors = data.get("authors", [])
        year = data.get("year")
        title = data.get("title", "")
        journal = data.get("journal", "")
        volume = data.get("volume", "")
        issue = data.get("issue", "")
        pages = data.get("pages", "")
        
        # 类型标记，默认为J（期刊文章）
        ref_type = "J"
        
        parts = []
        if authors:
            author_str = ", ".join(authors)
            parts.append(f"{author_str}.")
        if year:
            parts.append(f"{year}.")
        if title:
            parts.append(f"{title}[{ref_type}].")
        if journal:
            parts.append(journal)
        if volume:
            vol_info = f"{volume}"
            if issue:
                vol_info += f"({issue})"
            if pages:
                vol_info += f": {pages}"
            parts.append(vol_info)
        
        result = ", ".join(parts)
        if not result.endswith("."):
            result += "."
        return result
    
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
                formatted.append(self.format_gb2015(ref, idx))
            elif target_format == "numeric":
                formatted.append(self.format_numeric(ref, idx))
            elif target_format == "author_year":
                formatted.append(self.format_author_year(ref))
            else:
                # 原始格式
                formatted.append(ref.get("text", ""))
        
        return "\n".join(formatted)

