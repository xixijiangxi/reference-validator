import os
import json
import dashscope
from typing import List, Dict, Any
from dotenv import load_dotenv
import logging
from pathlib import Path

# 加载 .env 文件 - 明确指定 backend 目录，并处理 BOM
backend_dir = Path(__file__).parent.parent.parent
env_path = backend_dir / '.env'
if not env_path.exists():
    env_path = backend_dir / 'backend' / '.env'

# 如果文件存在，先处理 BOM（如果有）
if env_path.exists():
    try:
        with open(env_path, 'r', encoding='utf-8-sig') as f:
            content = f.read()
        # 重新写入，确保没有 BOM
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write(content)
    except Exception:
        pass  # 如果处理失败，继续尝试加载

load_dotenv(env_path, override=True)

logger = logging.getLogger(__name__)

# 检查 API Key
api_key = os.getenv("DASHSCOPE_API_KEY", "").strip()
dashscope.api_key = api_key

if api_key:
    logger.info(f"✓ 已加载 DASHSCOPE_API_KEY: {api_key[:10]}...")
else:
    logger.warning("✗ 未配置 DASHSCOPE_API_KEY，将使用本地规则拆分")


class LLMService:
    """大模型服务，用于参考文献拆分和关键词提取"""
    
    def __init__(self):
        self.model = "qwen-plus"  # 使用Qwen3 Plus模型
        
    def split_references(self, text: str) -> List[Dict[str, Any]]:
        """拆分参考文献列表"""
        prompt = f"""你是一个专业的医学科研论文专家，也是拥有多年经验的专业审稿人，熟悉常见参考文献著录格式的专家。请将以下文本拆分成独立的参考文献条目。

支持的参考文献格式包括：
1. 通用顺序编码制（如：[1] 作者. 标题. 期刊, 年份, 卷(期): 页码）
2. 通用著者出版年制（如：作者(年份). 标题. 期刊, 卷(期): 页码）
3. 国标2015（GB/T 7714-2015）
4. APA格式
5. MLA格式
6. AMA格式
7. NLM格式

参考文献格式示例：
1. 通用顺序编码制
规则说明：
引用序号用方括号标注，格式为：[序号] 作者. 标题. 期刊, 年份, 卷(期): 起止页码. DOI
[1] Ren R, Qi J, Lin S, et al. The China Alzheimer Report 2022. Gen Psychiatr, 2022, 35(1): e100751. doi:10.1136/gpsych-2022-100751
[2] Zhi N, Ren R, Qi J, et al. The China Alzheimer Report 2025. Gen Psychiatr, 2025, 38(4): e102020. doi:10.1136/gpsych-2024-102020
[3] Kelechi Wisdom E, Soyemi T, Mayowa S, et al. Building healthcare capacity for neurodegenerative disease management in Nigeria: Challenges and opportunities. J Public Health Res, 2025, 14(2): 22799036251350957. doi:10.1177/22799036251350957
[4] Yang Y, Qiu L. Research Progress on the Pathogenesis, Diagnosis, and Drug Therapy of Alzheimer's Disease. Brain Sci, 2024, 14(6): 590. doi:10.3390/brainsci14060590
2. 通用著者-出版年制
规则说明：
作者后标注出版年份，格式为：作者(年份). 标题. 期刊, 卷(期): 起止页码. DOI
Ren R, Qi J, Lin S, et al (2022). The China Alzheimer Report 2022. Gen Psychiatr, 35(1): e100751. doi:10.1136/gpsych-2022-100751
Zhi N, Ren R, Qi J, et al (2025). The China Alzheimer Report 2025. Gen Psychiatr, 38(4): e102020. doi:10.1136/gpsych-2024-102020
Kelechi Wisdom E, Soyemi T, Mayowa S, et al (2025). Building healthcare capacity for neurodegenerative disease management in Nigeria: Challenges and opportunities. J Public Health Res, 14(2): 22799036251350957. doi:10.1177/22799036251350957
Yang Y, Qiu L (2024). Research Progress on the Pathogenesis, Diagnosis, and Drug Therapy of Alzheimer's Disease. Brain Sci, 14(6): 590. doi:10.3390/brainsci14060590
3. 国标GB/T 7714-2015（顺序编码制）
规则说明：
采用电子文献格式：[序号] 作者. 题名[文献类型标识/文献载体标识]. 期刊名, 年, 卷(期): 页码[引用日期]. DOI.
[1] Ren R, Qi J, Lin S, et al. The China Alzheimer Report 2022[J/OL]. Gen Psychiatr, 2022, 35(1): e100751. doi:10.1136/gpsych-2022-100751.
[2] Zhi N, Ren R, Qi J, et al. The China Alzheimer Report 2025[J/OL]. Gen Psychiatr, 2025, 38(4): e102020. doi:10.1136/gpsych-2024-102020.
[3] Kelechi Wisdom E, Soyemi T, Mayowa S, et al. Building healthcare capacity for neurodegenerative disease management in Nigeria: challenges and opportunities[J/OL]. J Public Health Res, 2025, 14(2): 22799036251350957. doi:10.1177/22799036251350957.
[4] Yang Y, Qiu L. Research Progress on the Pathogenesis, Diagnosis, and Drug Therapy of Alzheimer's Disease[J/OL]. Brain Sci, 2024, 14(6): 590. doi:10.3390/brainsci14060590.
4. APA格式（第7版）
规则说明：
作者姓, 名首字母. (年份). 标题. 期刊斜体, 卷号(期号), 页码. https://doi.org/xxxx
Ren, R., Qi, J., Lin, S., Tang, Y., Dong, Q., Xu, W., & Yu, J. (2022). The China Alzheimer Report 2022. General Psychiatry, 35(1), e100751. https://doi.org/10.1136/gpsych-2022-100751
Zhi, N., Ren, R., Qi, J., Lin, S., Xu, W., Dong, Q., Wang, Y., Li, Y., & Yu, J. (2025). The China Alzheimer Report 2025. General Psychiatry, 38(4), e102020. https://doi.org/10.1136/gpsych-2024-102020
Kelechi Wisdom, E., Soyemi, T., Mayowa, S., Adebayo, O., & Oladipo, O. (2025). Building healthcare capacity for neurodegenerative disease management in Nigeria: Challenges and opportunities. Journal of Public Health Research, 14(2), 22799036251350957. https://doi.org/10.1177/22799036251350957
Yang, Y., & Qiu, L. (2024). Research progress on the pathogenesis, diagnosis, and drug therapy of Alzheimer's disease. Brain Sciences, 14(6), 590. https://doi.org/10.3390/brainsci14060590
5. MLA格式（第9版）
规则说明：
作者全名. "文章标题." 期刊名斜体, vol. #, no. #, 年份, pp. 页码. DOI或URL.
Ren, Ruoqi, et al. "The China Alzheimer Report 2022." General Psychiatry, vol. 35, no. 1, 2022, p. e100751. doi:10.1136/gpsych-2022-100751.
Zhi, Na, et al. "The China Alzheimer Report 2025." General Psychiatry, vol. 38, no. 4, 2025, p. e102020. doi:10.1136/gpsych-2024-102020.
Kelechi Wisdom, Emmanuel, et al. "Building Healthcare Capacity for Neurodegenerative Disease Management in Nigeria: Challenges and Opportunities." Journal of Public Health Research, vol. 14, no. 2, 2025, p. 22799036251350957. doi:10.1177/22799036251350957.
Yang, Yan, and Li Qiu. "Research Progress on the Pathogenesis, Diagnosis, and Drug Therapy of Alzheimer's Disease." Brain Sciences, vol. 14, no. 6, 2024, p. 590. doi:10.3390/brainsci14060590.
6. AMA格式（第11版）
规则说明：
作者姓 名首字母. 标题. 期刊名缩写. 年份;卷号(期号):页码. doi:xxxx
Ren R, Qi J, Lin S, et al. The China Alzheimer Report 2022. Gen Psychiatr. 2022;35(1):e100751. doi:10.1136/gpsych-2022-100751
Zhi N, Ren R, Qi J, et al. The China Alzheimer Report 2025. Gen Psychiatr. 2025;38(4):e102020. doi:10.1136/gpsych-2024-102020
Kelechi Wisdom E, Soyemi T, Mayowa S, et al. Building Healthcare Capacity for Neurodegenerative Disease Management in Nigeria: Challenges and Opportunities. J Public Health Res. 2025;14(2):22799036251350957. doi:10.1177/22799036251350957
Yang Y, Qiu L. Research Progress on the Pathogenesis, Diagnosis, and Drug Therapy of Alzheimer’s Disease. Brain Sci. 2024;14(6):590. doi:10.3390/brainsci14060590
7. NLM格式
规则说明：
作者. 标题. 期刊名. 年份;卷号(期号):页码. doi:xxxx（期刊名使用NLM标准缩写）
Ren R, Qi J, Lin S, Tang Y, Dong Q, Xu W, Yu J. The China Alzheimer Report 2022. Gen Psychiatr. 2022;35(1):e100751. doi:10.1136/gpsych-2022-100751
Zhi N, Ren R, Qi J, Lin S, Xu W, Dong Q, Wang Y, Li Y, Yu J. The China Alzheimer Report 2025. Gen Psychiatr. 2025;38(4):e102020. doi:10.1136/gpsych-2024-102020
Kelechi Wisdom E, Soyemi T, Mayowa S, Adebayo O, Oladipo O. Building healthcare capacity for neurodegenerative disease management in Nigeria: challenges and opportunities. J Public Health Res. 2025;14(2):22799036251350957. doi:10.1177/22799036251350957
Yang Y, Qiu L. Research progress on the pathogenesis, diagnosis, and drug therapy of Alzheimer's disease. Brain Sci. 2024;14(6):590. doi:10.3390/brainsci14060590
格式要点说明：
顺序编码制和著者-出版年制为国内常用格式
GB/T 7714-2015是中国国家标准，支持双语引用
APA 7强调DOI和超链接格式
MLA 9对作者姓名和标题大小写有严格要求
AMA 11使用期刊标准缩写，句末使用句号
NLM格式采用PubMed标准，期刊名需使用NLM官方缩写
【任务】
1、请识别每条参考文献的边界（如果有多余字符请删除，如被切断请合并），根据用户输入的内容识别有几条参考文献。
2、识别用户输入的参考文献的格式，如果你觉得不属于任何一种标准格式，请返回"original"。
需要返回JSON格式的结果。

输入文本：
{text}

请返回JSON数组格式，每个元素包含：
{{
    "id": "唯一标识符（如ref_1）",
    "text": "完整的参考文献文本",
    "format_type": "识别的格式类型（如：numeric, author_year, apa, mla, ama, nlm, gb2015,original）"
}}

只返回JSON数组，不要添加任何其他说明文字。"""

        try:
            if not api_key:
                logger.warning("未配置 API Key，使用本地规则拆分")
                return self._basic_split(text)
            
            logger.info("调用 LLM API 拆分参考文献...")
            response = dashscope.Generation.call(
                model=self.model,
                prompt=prompt,
                temperature=0.1,
                max_tokens=4000,
                response_format={'type': 'json_object'} 
            )
            
            if response is None:
                logger.error("LLM API 返回 None，使用本地规则拆分")
                return self._basic_split(text)
            
            logger.info(f"LLM API 响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                if response.output is None:
                    logger.error("LLM API 响应中 output 为 None，使用本地规则拆分")
                    return self._basic_split(text)
                
                if not hasattr(response.output, 'choices') or not response.output.choices:
                    logger.error("LLM API 响应中 choices 为空，使用本地规则拆分")
                    return self._basic_split(text)
                
                if len(response.output.choices) == 0:
                    logger.error("LLM API 响应中 choices 列表为空，使用本地规则拆分")
                    return self._basic_split(text)
                
                choice = response.output.choices[0]
                if not hasattr(choice, 'message') or choice.message is None:
                    logger.error("LLM API 响应中 message 为 None，使用本地规则拆分")
                    return self._basic_split(text)
                
                if not hasattr(choice.message, 'content') or choice.message.content is None:
                    logger.error("LLM API 响应中 content 为 None，使用本地规则拆分")
                    return self._basic_split(text)
                
                content = choice.message.content.strip()
                logger.info(f"LLM 返回内容长度: {len(content)} 字符")
                
                # 尝试提取JSON部分
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                
                try:
                    references = json.loads(content)
                    if isinstance(references, list):
                        logger.info(f"LLM 成功解析，返回 {len(references)} 条参考文献")
                        return references
                    else:
                        logger.info(f"LLM 返回单个对象，转换为列表")
                        return [references]
                except json.JSONDecodeError as e:
                    logger.error(f"LLM 返回内容不是有效的 JSON: {e}")
                    logger.error(f"内容预览: {content[:200]}...")
                    logger.info("JSON 解析失败，使用本地规则拆分")
                    return self._basic_split(text)
            else:
                error_msg = getattr(response, 'message', 'Unknown error')
                logger.error(f"LLM API错误: status_code={response.status_code}, message={error_msg}")
                # LLM 调用失败，使用本地规则作为后备
                logger.info("LLM API 返回错误，使用本地规则拆分")
                return self._basic_split(text)
        except Exception as e:
            logger.error(f"拆分参考文献时出错: {str(e)}", exc_info=True)
            # LLM 调用失败，使用本地规则作为后备
            logger.info("LLM 调用失败，使用本地规则拆分")
            return self._basic_split(text)
    
    def extract_keywords(self, reference_text: str) -> Dict[str, Any]:
        """从参考文献文本中提取关键词"""
        prompt = f"""你是一个专业的医学科研论文专家，也是拥有多年经验的专业审稿人，熟悉常见参考文献著录格式的专家。请从以下参考文献文本中提取所有可识别的信息。

请提取以下字段（如果存在）：
- title: 文章标题
- authors: 作者列表（数组格式）
- journal: 期刊名称
- year: 出版年份（整数）
- volume: 卷号
- issue: 期号
- pages: 页码（如：123-128）
- pmid: PubMed ID
- doi: DOI号

参考文献文本：
{reference_text}

请返回JSON格式，只包含存在的字段：
{{
    "title": "文章标题",
    "authors": ["作者1", "作者2"],
    "journal": "期刊名称",
    "year": 2023,
    "volume": "卷号",
    "issue": "期号",
    "pages": "页码",
    "pmid": "PMID号",
    "doi": "DOI号"
}}

只返回JSON对象，不要添加任何其他说明文字。如果某个字段不存在，请不要包含该字段。"""

        try:
            if not api_key:
                logger.warning("未配置 API Key，使用本地规则提取")
                return self._basic_extract_keywords(reference_text)
            
            logger.info("调用 LLM API 提取关键词...")
            response = dashscope.Generation.call(
                model=self.model,
                prompt=prompt,
                temperature=0.1,
                max_tokens=2000,
                response_format={'type': 'json_object'}
            )
            
            if response is None:
                logger.error("LLM API 返回 None，使用本地规则提取")
                return self._basic_extract_keywords(reference_text)
            
            logger.info(f"LLM API 响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                if response.output is None:
                    logger.error("LLM API 响应中 output 为 None，使用本地规则提取")
                    return self._basic_extract_keywords(reference_text)
                
                if not hasattr(response.output, 'choices') or not response.output.choices:
                    logger.error("LLM API 响应中 choices 为空，使用本地规则提取")
                    return self._basic_extract_keywords(reference_text)
                
                if len(response.output.choices) == 0:
                    logger.error("LLM API 响应中 choices 列表为空，使用本地规则提取")
                    return self._basic_extract_keywords(reference_text)
                
                choice = response.output.choices[0]
                if not hasattr(choice, 'message') or choice.message is None:
                    logger.error("LLM API 响应中 message 为 None，使用本地规则提取")
                    return self._basic_extract_keywords(reference_text)
                
                if not hasattr(choice.message, 'content') or choice.message.content is None:
                    logger.error("LLM API 响应中 content 为 None，使用本地规则提取")
                    return self._basic_extract_keywords(reference_text)
                
                content = choice.message.content.strip()
                logger.info(f"LLM 返回内容长度: {len(content)} 字符")
                
                # 尝试提取JSON部分
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                
                try:
                    keywords = json.loads(content)
                    logger.info(f"LLM 成功解析关键词")
                    return keywords
                except json.JSONDecodeError as e:
                    logger.error(f"LLM 返回内容不是有效的 JSON: {e}")
                    logger.error(f"内容预览: {content[:200]}...")
                    logger.info("JSON 解析失败，使用本地规则提取")
                    return self._basic_extract_keywords(reference_text)
            else:
                error_msg = getattr(response, 'message', 'Unknown error')
                logger.error(f"LLM API错误: status_code={response.status_code}, message={error_msg}")
                logger.info("LLM API 返回错误，使用本地规则提取")
                return self._basic_extract_keywords(reference_text)
        except Exception as e:
            logger.error(f"提取关键词时出错: {str(e)}", exc_info=True)
            logger.info("LLM 调用失败，使用本地规则提取")
            return self._basic_extract_keywords(reference_text)
    
    def _basic_split(self, text: str) -> List[Dict[str, Any]]:
        """基于简单规则拆分参考文献，保证无LLM时也能工作"""
        logger.info("使用本地规则拆分参考文献")
        import re
        
        entries = re.split(r'(?:\r?\n){2,}', text)
        if len(entries) == 1:
            entries = [line.strip() for line in text.splitlines() if line.strip()]
        else:
            entries = [entry.strip() for entry in entries if entry.strip()]

        references = []
        for idx, entry in enumerate(entries, start=1):
            normalized = entry.strip().strip('""" ')
            if not normalized:
                continue
            references.append(
                {
                    "id": f"ref_{idx}",
                    "text": normalized,
                    "format_type": self._guess_format(normalized),
                }
            )
        return references
    
    def _guess_format(self, reference_text: str) -> str:
        """猜测参考文献格式"""
        import re
        if re.match(r'^\[\d+\]', reference_text):
            return "numeric"
        if re.search(r'\(\d{4}\)', reference_text):
            return "author_year"
        if "doi" in reference_text.lower():
            return "apa"
        if re.search(r'\d{4}\.\s', reference_text):
            return "ama"
        return "original"
    
    def _basic_extract_keywords(self, reference_text: str) -> Dict[str, Any]:
        """基础的关键词提取方法，使用简单规则"""
        logger.info("使用本地规则提取关键词")
        import re
        
        text = reference_text.strip()
        result: Dict[str, Any] = {}

        # 标题 - 优先提取引号内的内容
        title_match = re.findall(r'"([^"]+)"', text)
        if title_match:
            result["title"] = title_match[0].strip()
        else:
            # 尝试提取 " - " 前的部分作为标题
            if " - " in text:
                candidate = text.split(" - ")[0].strip('""" ')
                if len(candidate.split()) > 2:
                    result["title"] = candidate
            else:
                # 处理格式：[序号] 作者. 标题. 期刊...
                # 或：作者. 标题. 期刊...
                # 标题通常在第一个句号和第二个句号之间
                # 先移除序号
                text_clean = re.sub(r'^\[\d+\]\s*', '', text)
                # 查找作者部分（通常以大写字母开头，以句号结尾）
                # 然后标题是下一个句号之前的内容
                parts = text_clean.split('.')
                if len(parts) >= 2:
                    # 第一部分通常是作者，第二部分可能是标题
                    # 但需要判断：如果第二部分很短（<5个词），可能是作者的一部分
                    potential_title = parts[1].strip() if len(parts) > 1 else ""
                    if len(potential_title.split()) >= 3:
                        result["title"] = potential_title
                    elif len(parts) >= 3:
                        # 如果第二部分太短，尝试第三部分
                        potential_title = parts[2].strip()
                        if len(potential_title.split()) >= 3:
                            result["title"] = potential_title

        # 年份（先提取，后面会用到）
        year_match = re.search(r'\b(19|20)\d{2}\b', text)
        if year_match:
            result["year"] = int(year_match.group(0))

        # 作者 - 处理多种格式
        authors = []
        
        if " - " in text and result.get("title"):
            # 提取 " - " 后的部分
            after_dash = text.split(" - ", 1)[1]
            
            # 提取到 "et al" 或年份之前的部分
            author_part = re.split(r',?\s+et al|[,;]\s*\d{4}', after_dash)[0]
            author_part = author_part.strip(', ')
            
            # 处理 "Montague, P.R." 这种格式
            author_matches = re.findall(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)[,\s]+([A-Z]\.?(?:\s*[A-Z]\.?)*)', author_part)
            if author_matches:
                for last, first in author_matches:
                    full_name = f"{last}, {first}".strip()
                    authors.append(full_name)
        else:
            # 处理格式：[序号] 作者. 标题. 期刊...
            # 作者在第一个句号之前
            text_clean = re.sub(r'^\[\d+\]\s*', '', text)
            parts = text_clean.split('.')
            if len(parts) > 0:
                author_part = parts[0].strip()
                # 处理 "Doroszkiewicz J, Mroczko B" 或 "Zhao Q, Du X, Chen W, Zhang T, Xu Z" 格式
                # 分割逗号，每个部分是一个作者
                author_names = [name.strip() for name in author_part.split(',') if name.strip()]
                for name in author_names:
                    # 排除 "et al"
                    if name.lower() in ['et al', 'et', 'al']:
                        break  # 遇到 et al 就停止
                    # 处理 "Doroszkiewicz J" 格式（姓 名首字母）
                    name_parts = name.split()
                    if len(name_parts) >= 2:
                        last_name = name_parts[0]
                        first_initial = name_parts[1]
                        authors.append(f"{last_name}, {first_initial}")
                    elif len(name_parts) == 1:
                        # 只有姓，直接添加
                        authors.append(name_parts[0])
        
        # 如果没有找到作者，尝试其他模式
        if not authors:
            author_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)[,\s]+([A-Z]\.?(?:\s*[A-Z]\.?)*)'
            author_matches = re.findall(author_pattern, text)
            if author_matches:
                authors = [f"{last}, {first}".strip() for last, first in author_matches[:5]]
        
        if authors:
            result["authors"] = authors

        # 期刊 - 多种模式
        journal_match = re.search(r'\d{4}[,;]\s+([^,;.]+?)[,;.]', text)
        if journal_match:
            journal = journal_match.group(1).strip()
            if not re.match(r'^(Volume|Vol\.?|v\.?)\s*\d+', journal, re.IGNORECASE):
                result["journal"] = journal
        
        # 模式2: 期刊名通常在标题和年份之间
        if not result.get("journal") and result.get("title") and result.get("year"):
            title_end = text.find(result["title"]) + len(result["title"])
            year_start = text.find(str(result["year"]))
            if title_end > 0 and year_start > title_end:
                between = text[title_end:year_start].strip(' ,-.')
                between = re.sub(r'^[-,;.]\s*', '', between)
                between = re.sub(r'\s*[-,;.]\s*$', '', between)
                # 如果包含冒号和数字（如 "17:1216215"），只取冒号前的部分
                if ':' in between:
                    between = between.split(':')[0].strip()
                # 如果包含 "Published"，只取之前的部分
                if 'Published' in between:
                    between = between.split('Published')[0].strip()
                # 移除末尾的数字（卷号）
                between = re.sub(r'\s+\d+$', '', between)
                between = between.rstrip('.,;')
                if between and len(between) > 3 and not between.isdigit():
                    result["journal"] = between
        
        # 模式3: 处理格式 作者. 标题. 期刊. 年份
        if not result.get("journal") and result.get("title"):
            text_clean = re.sub(r'^\[\d+\]\s*', '', text)
            parts = text_clean.split('.')
            # 找到标题所在的部分
            for i, part in enumerate(parts):
                if result["title"] in part:
                    # 期刊可能是下一个部分
                    if i + 1 < len(parts):
                        potential_journal = parts[i + 1].strip()
                        # 如果包含数字和冒号（如 "17:1216215"），只取冒号前的部分
                        if ':' in potential_journal:
                            potential_journal = potential_journal.split(':')[0].strip()
                        # 排除包含 "Published" 的部分
                        if 'Published' in potential_journal:
                            potential_journal = potential_journal.split('Published')[0].strip()
                        # 如果以数字开头或结尾，可能是卷号，需要进一步处理
                        # 例如 "Front Neurosci 17" -> "Front Neurosci"
                        potential_journal = re.sub(r'\s+\d+$', '', potential_journal)  # 移除末尾的数字
                        potential_journal = re.sub(r'^\d+\s+', '', potential_journal)  # 移除开头的数字
                        # 清理末尾的标点
                        potential_journal = potential_journal.rstrip('.,;')
                        # 如果清理后只剩下数字，跳过
                        if (potential_journal and 
                            len(potential_journal) > 2 and 
                            not potential_journal.isdigit() and
                            not re.match(r'^\d{4}', potential_journal) and
                            'Volume' not in potential_journal and
                            'Vol' not in potential_journal):
                            result["journal"] = potential_journal
                            break

        # 卷号与期号
        # 模式1: Volume 16 或 Vol. 16
        volume_match = re.search(r'(?:Volume|Vol\.?|v\.?)\s*(\d+)', text, re.IGNORECASE)
        if volume_match:
            result["volume"] = volume_match.group(1)
        else:
            # 模式2: 年份;卷号(期号) 如 2025;97(1)
            vol_issue_match = re.search(r'\d{4};\s*(\d+)\((\d+)\)', text)
            if vol_issue_match:
                result["volume"] = vol_issue_match.group(1)
                result["issue"] = vol_issue_match.group(2)
            else:
                # 模式3: 卷号(期号) 如 97(1)
                vol_issue_match2 = re.search(r'\b(\d+)\((\d+)\)', text)
                if vol_issue_match2:
                    result["volume"] = vol_issue_match2.group(1)
                    result["issue"] = vol_issue_match2.group(2)
                else:
                    # 模式4: 期刊. 卷号:页码 如 "Front Neurosci. 17:1216215"
                    # 这种格式中，卷号在期刊后的数字
                    if result.get("journal"):
                        # 在期刊名后查找数字
                        journal_pos = text.find(result["journal"])
                        if journal_pos >= 0:
                            after_journal = text[journal_pos + len(result["journal"]):]
                            # 查找第一个数字（可能是卷号）
                            vol_match = re.search(r'\.\s*(\d+)[:;\(]', after_journal)
                            if vol_match:
                                result["volume"] = vol_match.group(1)
        
        if not result.get("issue"):
            issue_match = re.search(r'(?:Issue|No\.?|#)\s*(\d+)', text, re.IGNORECASE)
            if issue_match:
                result["issue"] = issue_match.group(1)

        # 页码
        pages_match = re.search(r':?\s*(\d+)\s*[-–]\s*(\d+)', text)
        if pages_match:
            result["pages"] = f"{pages_match.group(1)}-{pages_match.group(2)}"

        # DOI
        doi_match = re.search(r'(?:doi:?\s*)?(\b10\.\d{4,9}/[^\s,;]+)', text, re.IGNORECASE)
        if doi_match:
            result["doi"] = doi_match.group(1).rstrip('.,;')

        # PMID
        # 模式1: PMID: 12345678
        pmid_match = re.search(r'PMID:?\s*(\d+)', text, re.IGNORECASE)
        if pmid_match:
            result["pmid"] = pmid_match.group(1)
        else:
            # 模式2: 从URL中提取 pubmed.ncbi.nlm.nih.gov/12345678
            url_match = re.search(r'pubmed\.ncbi\.nlm\.nih\.gov/(\d+)', text, re.IGNORECASE)
            if url_match:
                result["pmid"] = url_match.group(1)

        return result

