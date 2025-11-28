export interface ReferenceKeyword {
  title?: string;
  authors?: string[];
  journal?: string;
  year?: number;
  volume?: string;
  issue?: string;
  pages?: string;
  pmid?: string;
  doi?: string;
}

export interface PubMedArticle {
  pmid?: string;
  title?: string;
  authors?: string[];
  journal?: string;
  year?: number;
  volume?: string;
  issue?: string;
  pages?: string;
  doi?: string;
  abstract?: string;
  keywords: ReferenceKeyword;
  similarity_score: number;
  differences: Record<string, any>;
  match_type?: string; // "doi_match" 或 "pmid_match"，表示通过DOI或PMID匹配到的文章
}

export interface ReferenceItem {
  id: string;
  original_text: string;
  format_type?: string;
  extracted_keywords: ReferenceKeyword;
  matched_articles: PubMedArticle[];
  status: "pending" | "matched" | "not_found" | "completed";
}

export interface ProcessedReference {
  id: string;
  text: string;
  data: ReferenceKeyword;
  format_type?: string;
}

